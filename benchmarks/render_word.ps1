param([Parameter(Mandatory = $true)][string]$Batch)

# Opens only generated DOCX files in a private hidden Word instance.
# No source PDFs are opened in Word; no pre-existing Word session is reused.
$ErrorActionPreference = 'Stop'
$batchPath = (Resolve-Path -LiteralPath $Batch).Path
$artifactRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\.generated')) + '\'
if (-not $batchPath.StartsWith($artifactRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The batch must be inside this workspace .generated directory.'
}
$cases = (Get-Content -LiteralPath $batchPath -Encoding UTF8 -Raw | ConvertFrom-Json).cases
foreach ($item in $cases) {
    foreach ($field in @('docx', 'pdf', 'edited_docx', 'word_report')) {
        $artifactPath = [System.IO.Path]::GetFullPath($item.$field)
        if (-not $artifactPath.StartsWith($artifactRoot, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Word artifact path is outside the generated workspace.'
        }
    }
}
$wordApp = $null
$document = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordApp.AutomationSecurity = 3
    foreach ($item in $cases) {
        try {
            $document = $wordApp.Documents.Open($item.docx, $false, $true)
            $pages = $document.ComputeStatistics(2)
            $document.ExportAsFixedFormat($item.pdf, 17)
            $paragraphEdited = $false
            foreach ($paragraph in $document.Paragraphs) {
                if ($paragraph.Range.Text.Trim().Length -gt 0 -and -not $paragraph.Range.Information(12)) {
                    $editRange = $paragraph.Range.Duplicate
                    $editRange.End = $editRange.End - 1
                    $editRange.InsertAfter(' [F0_EDIT_TEST]')
                    $paragraphEdited = $true
                    break
                }
            }
            $tableEdited = $false
            $tableColumns = $null
            $tableTarget = $null
            foreach ($candidate in $document.Tables) {
                if ($candidate.Columns.Count -gt 1) { $tableTarget = $candidate; break }
            }
            if (-not $tableTarget -and $document.Tables.Count -gt 0) { $tableTarget = $document.Tables.Item(1) }
            if ($tableTarget) {
                $tableColumns = $tableTarget.Columns.Count
                $tableTarget.Cell(1, 1).Range.Text = '[F0_CELL_EDIT_TEST]'
                $tableEdited = $true
            }
            $document.SaveAs2($item.edited_docx, 16)
            $document.Close(0)
            $document = $wordApp.Documents.Open($item.edited_docx, $false, $true)
            $text = $document.Content.Text
            $result = [ordered]@{
                id = $item.id
                word_version = $wordApp.Version
                rendered_pages = $pages
                paragraph_edit_save_reopen = ($paragraphEdited -and $text.Contains('[F0_EDIT_TEST]'))
                table_edit_save_reopen = $(if ($tableEdited) { $text.Contains('[F0_CELL_EDIT_TEST]') } else { $null })
                edited_table_columns = $tableColumns
            }
            $result | ConvertTo-Json | Set-Content -LiteralPath $item.word_report -Encoding UTF8
            Write-Output "$($item.id): Word rendered $pages pages; edit/reopen checked."
        } finally {
            if ($document) { $document.Close(0); $document = $null }
        }
    }
} finally {
    if ($wordApp) { $wordApp.Quit() }
}
