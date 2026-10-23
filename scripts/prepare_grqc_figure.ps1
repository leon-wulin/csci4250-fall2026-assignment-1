$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$dir=Join-Path $root 'results/gephi'
[xml]$svg=[IO.File]::ReadAllText((Join-Path $dir 'grqc_layout_base.svg'))
[xml]$graph=[IO.File]::ReadAllText((Join-Path $root 'data/processed/task2/grqc_real.graphml'))
$degree=@{};$edgeSet=[Collections.Generic.HashSet[string]]::new()
foreach($n in $graph.SelectNodes('//*[local-name()="node"]')){$degree[$n.id]=0}
foreach($e in $graph.SelectNodes('//*[local-name()="edge"]')){$degree[$e.source]++;$degree[$e.target]++;[void]$edgeSet.Add((@([int]$e.source,[int]$e.target)|Sort-Object)-join ':')}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[IO.Compression.ZipFile]::OpenRead((Join-Path $dir 'network_visualizations.gephi'))
$reader=[IO.StreamReader]::new($zip.GetEntry('Workspace_2_appearancemodel_xml').Open());[xml]$appearance=$reader.ReadToEnd();$reader.Dispose();$zip.Dispose()
$mapping=@{}
foreach($c in $appearance.SelectNodes('//partition[@column="modularity_class"]/color')){
 $rgb=([long]$c.rgba -band 0xffffff).ToString('x6');$mapping["#$rgb"]=[int]$c.for
}
$culture=[Globalization.CultureInfo]::InvariantCulture
$nodes=@();$seen=[Collections.Generic.HashSet[string]]::new()
foreach($n in $svg.SelectNodes('//*[local-name()="circle"]')){
 $id=$n.GetAttribute('class').Substring(3);if(-not $degree.ContainsKey($id) -or -not $seen.Add($id)){throw 'Unknown/duplicate node'}
 $fill=$n.GetAttribute('fill');$community=$null;if($mapping.ContainsKey($fill)){$community=$mapping[$fill]}
 $nodes+=@{id=$id;x=[double]::Parse($n.cx,$culture);y=[double]::Parse($n.cy,$culture);degree=$degree[$id];community=$community;originalColor=$fill}
}
$edges=@();$seenEdges=[Collections.Generic.HashSet[string]]::new()
foreach($e in $svg.SelectNodes('//*[local-name()="path"]')){
 $ids=$e.GetAttribute('class').Split(' ');$s=$ids[0].Substring(3);$t=$ids[1].Substring(3)
 $key=(@([int]$s,[int]$t)|Sort-Object)-join ':'
 if(-not $edgeSet.Contains($key) -or -not $seenEdges.Add($key)){throw 'Topology mismatch'}
 $edges+=@{source=$s;target=$t}
}
if($nodes.Count -ne 5242 -or $edges.Count -ne 14484 -or -not $edgeSet.SetEquals($seenEdges)){throw 'Count mismatch'}
@{nodes=$nodes;edges=$edges;mapping=$mapping;validated=$true}|ConvertTo-Json -Depth 6 -Compress|Set-Content (Join-Path $dir 'grqc_figure_scene.json') -Encoding utf8
Write-Output 'Validated 5242 nodes and 14484 edges against frozen GraphML; community-color mapping recovered from saved project.'
