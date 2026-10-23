# Convert frozen analyzed GraphML inputs to GML without changing topology.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$outputDir = Join-Path $projectRoot 'results/gephi'
[IO.Directory]::CreateDirectory($outputDir) | Out-Null
$audit = @()
foreach ($name in @('power_real', 'grqc_real')) {
    $source = Join-Path $projectRoot "data/processed/task2/$name.graphml"
    $destination = Join-Path $outputDir "$name.gml"
    if (Test-Path -LiteralPath $destination) { throw "Output already exists: $destination" }
    [xml]$document = [IO.File]::ReadAllText($source)
    $nodes = @($document.SelectNodes('//*[local-name()="node"]'))
    $edges = @($document.SelectNodes('//*[local-name()="edge"]'))
    $ids = [Collections.Generic.HashSet[string]]::new()
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add('graph [')
    $lines.Add('  directed 0')
    foreach ($node in $nodes) {
        $id = $node.GetAttribute('id')
        if ($id -notmatch '^\d+$' -or -not $ids.Add($id)) { throw 'Invalid node ID' }
        $lines.Add("  node [ id $id label `"$id`" ]")
    }
    $edgeSet = [Collections.Generic.HashSet[string]]::new()
    foreach ($edge in $edges) {
        $s = $edge.GetAttribute('source'); $t = $edge.GetAttribute('target')
        if (-not $ids.Contains($s) -or -not $ids.Contains($t)) { throw 'Unknown endpoint' }
        $key = (@([long]$s, [long]$t) | Sort-Object) -join ':'
        if (-not $edgeSet.Add($key)) { throw 'Duplicate edge' }
        $lines.Add("  edge [ source $s target $t ]")
    }
    $lines.Add(']')
    [IO.File]::WriteAllLines($destination, $lines, [Text.Encoding]::ASCII)
    $saved = [IO.File]::ReadAllText($destination)
    $savedNodes = [regex]::Matches($saved, 'node \[ id (\d+) label "(\d+)" \]')
    $savedEdges = [regex]::Matches($saved, 'edge \[ source (\d+) target (\d+) \]')
    $roundTripNodes = [Collections.Generic.HashSet[string]]::new()
    foreach ($match in $savedNodes) { [void]$roundTripNodes.Add($match.Groups[1].Value) }
    $roundTripEdges = [Collections.Generic.HashSet[string]]::new()
    foreach ($match in $savedEdges) {
        [void]$roundTripEdges.Add(((@([long]$match.Groups[1].Value, [long]$match.Groups[2].Value) | Sort-Object) -join ':'))
    }
    if (-not $ids.SetEquals($roundTripNodes) -or -not $edgeSet.SetEquals($roundTripEdges)) { throw 'Round-trip topology mismatch' }
    $audit += [pscustomobject]@{ graph=$name; nodes=$nodes.Count; edges=$edges.Count; topologyVerified=$true; sourceSHA256=(Get-FileHash -LiteralPath $source).Hash; outputSHA256=(Get-FileHash -LiteralPath $destination).Hash }
}
$audit | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputDir 'gml_conversion_audit.json') -Encoding utf8
$audit | Format-Table graph,nodes,edges,topologyVerified
