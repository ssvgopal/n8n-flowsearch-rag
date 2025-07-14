# Simple script to check for common secret patterns
$patterns = @(
    # API Keys
    '[a-z0-9]{32}',
    'AKIA[0-9A-Z]{16}',
    'AIza[0-9A-Za-z\-_]{35}',
    'sk_[a-zA-Z0-9]{32,}',
    'xox[baprs]-[0-9a-zA-Z]{10,48}',
    
    # OAuth
    'ya29\.[0-9A-Za-z\-_]+',
    
    # Passwords
    'password[=:].{8,}',
    'passwd[=:].{8,}',
    'pwd[=:].{8,}',
    'secret[=:].{8,}',
    'key[=:].{8,}',
    'token[=:].{8,}',
    
    # Database
    'postgres://[a-zA-Z0-9_]+:[^@]+@',
    'mysql://[a-zA-Z0-9_]+:[^@]+@',
    'mongodb://[a-zA-Z0-9_]+:[^@]+@'
)

Write-Host "Scanning for potential secrets..." -ForegroundColor Yellow

$found = $false

Get-ChildItem -Path . -Recurse -File | Where-Object { 
    $_.FullName -notmatch '\\.git|\\node_modules|\\venv|\\.venv|\\.env' -and
    $_.Extension -notin @('.dll','.exe','.png','.jpg','.jpeg','.gif','.pdf','.zip','.tar','.gz')
} | ForEach-Object {
    $filePath = $_.FullName
    $content = Get-Content -Path $filePath -Raw -ErrorAction SilentlyContinue
    
    if ($content) {
        $patterns | ForEach-Object {
            if ($content -match $_) {
                $found = $true
                $line = [regex]::Match($content, $_, 'Multiline').Value
                Write-Host "Potential secret found in: $filePath" -ForegroundColor Red
                Write-Host "  Pattern: $_" -ForegroundColor Yellow
                Write-Host "  Match: $line" -ForegroundColor Red
                Write-Host ""
            }
        }
    }
}

if (-not $found) {
    Write-Host "No obvious secrets found. However, please review the code manually as well." -ForegroundColor Green
} else {
    Write-Host "Potential secrets found. Please review these before publishing." -ForegroundColor Red
}

Write-Host "Secret scan complete." -ForegroundColor Green
