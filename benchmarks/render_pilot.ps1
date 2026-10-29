param([Parameter(Mandatory = $true)][string]$Batch)

# All input documents are generated artifacts. Office runs in private,
# hidden instances and only writes render/edit copies under .generated/.
$ErrorActionPreference = 'Stop'
$batchPath = (Resolve-Path -LiteralPath $Batch).Path
$artifactRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\.generated')) + '\'
function Assert-ArtifactPath([string]$Path) {
    if (-not ([System.IO.Path]::GetFullPath($Path)).StartsWith($artifactRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Office artifact path is outside this workspace .generated directory.'
    }
}
Assert-ArtifactPath $batchPath
$cases = (Get-Content -LiteralPath $batchPath -Encoding UTF8 -Raw | ConvertFrom-Json).cases
foreach ($item in $cases) {
    foreach ($field in @('docx', 'pdf', 'edited_docx', 'word_report', 'xlsx', 'edited_xlsx', 'excel_report')) {
        Assert-ArtifactPath $item.$field
    }
    foreach ($page in $item.excel_pages) { Assert-ArtifactPath $page.pdf }
}

$pendingWord = @($cases | Where-Object { -not (Test-Path -LiteralPath $_.word_report) })
foreach ($item in $pendingWord) {
    foreach ($field in @('pdf', 'edited_docx')) {
        if (Test-Path -LiteralPath $item.$field) { throw 'Partial Word outputs exist; use a new pilot directory.' }
    }
}
if ($pendingWord.Count -gt 0) {
    $wordBatch = Join-Path (Split-Path -Parent $batchPath) 'office-word-batch.json'
    @{ cases = $pendingWord } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $wordBatch -Encoding UTF8
    & (Join-Path $PSScriptRoot 'render_word.ps1') -Batch $wordBatch
}

$excel = $null
$book = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    foreach ($item in $cases) {
        if (Test-Path -LiteralPath $item.excel_report) { continue }
        foreach ($path in @($item.edited_xlsx) + @($item.excel_pages | ForEach-Object { $_.pdf })) {
            if (Test-Path -LiteralPath $path) { throw 'Partial Excel outputs exist; use a new pilot directory.' }
        }
        try {
            $book = $excel.Workbooks.Open($item.xlsx, 0, $true)
            $rendered = @()
            foreach ($page in $item.excel_pages) {
                $sheet = $book.Worksheets.Item($page.sheet)
                $sheet.Activate()
                $sheet.PageSetup.PrintArea = $sheet.UsedRange.Address()
                $sheet.PageSetup.PaperSize = $(if ([Math]::Abs([Math]::Max($page.width, $page.height) - 792) -lt 2) { 1 } else { 9 })
                $sheet.PageSetup.Orientation = $(if ($page.width -gt $page.height) { 2 } else { 1 })
                $sheet.PageSetup.Zoom = $false
                $sheet.PageSetup.FitToPagesWide = 1
                $sheet.PageSetup.FitToPagesTall = 1
                foreach ($side in @('Left', 'Right', 'Top', 'Bottom', 'Header', 'Footer')) {
                    $sheet.PageSetup.($side + 'Margin') = 0
                }
                foreach ($position in @('Left', 'Center', 'Right')) {
                    $sheet.PageSetup.($position + 'Header') = ''
                    $sheet.PageSetup.($position + 'Footer') = ''
                }
                $sheet.ExportAsFixedFormat(0, $page.pdf)
                $rendered += @{ sheet = $page.sheet; page = $page.page; pdf = $page.pdf }
            }
            $targetSheet = $book.Worksheets.Item($item.excel_pages[0].sheet)
            $targetCell = $null
            foreach ($cell in $targetSheet.UsedRange.Cells) {
                if ($null -ne $cell.Value2 -and ([string]$cell.Value2).Trim().Length -gt 0) { $targetCell = $cell; break }
            }
            if (-not $targetCell) { throw 'No editable text cell found in the first Excel page.' }
            $coordinate = $targetCell.Address()
            $targetSheetName = [string]$targetSheet.Name
            $targetCell.Value2 = ([string]$targetCell.Value2) + ' [PILOT_EDIT_TEST]'
            $book.SaveCopyAs($item.edited_xlsx)
            $book.Close($false)
            $book = $excel.Workbooks.Open($item.edited_xlsx, 0, $true)
            $editPassed = ([string]$book.Worksheets.Item($targetSheetName).Range($coordinate).Value2).Contains('[PILOT_EDIT_TEST]')
            $result = @{ id = $item.id; excel_version = $excel.Version; rendered = $rendered;
                         edit_save_reopen = $editPassed; edited_cell = $coordinate }
            $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $item.excel_report -Encoding UTF8
            Write-Output "$($item.id): Excel rendered $($rendered.Count) page sheets; edit/reopen=$editPassed."
        } finally {
            if ($book) { $book.Close($false); $book = $null }
        }
    }
} finally {
    if ($excel) { $excel.Quit() }
}
