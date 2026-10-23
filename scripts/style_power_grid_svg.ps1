# Restyle Gephi coordinates without modifying topology or original export.
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$folder=Join-Path $root 'results/gephi'
[xml]$svg=[IO.File]::ReadAllText((Join-Path $folder 'power_grid_layout_base.svg'))
[xml]$graph=[IO.File]::ReadAllText((Join-Path $root 'data/processed/task2/power_real.graphml'))
$degrees=@{}
foreach($n in $graph.SelectNodes('//*[local-name()="node"]')){$degrees[$n.id]=0}
foreach($e in $graph.SelectNodes('//*[local-name()="edge"]')){$degrees[$e.source]++;$degrees[$e.target]++}
$circles=@($svg.SelectNodes('//*[local-name()="circle"]'))
$paths=@($svg.SelectNodes('//*[local-name()="path"]'))
if($circles.Count -ne 4941 -or $paths.Count -ne 6594){throw 'Unexpected export counts'}
$culture=[Globalization.CultureInfo]::InvariantCulture
function Num($value){([double]$value).ToString('0.####',$culture)}
$positions=@{}
foreach($c in $circles){$id=$c.GetAttribute('class').Substring(3);if(-not $degrees.ContainsKey($id)){throw 'Unknown SVG ID'};$positions[$id]=@([double]::Parse($c.cx,$culture),[double]::Parse($c.cy,$culture))}
$xs=@($positions.Values | ForEach-Object {$_[0]});$ys=@($positions.Values | ForEach-Object {$_[1]})
$xmin=($xs|Measure-Object -Minimum).Minimum;$xmax=($xs|Measure-Object -Maximum).Maximum
$ymin=($ys|Measure-Object -Minimum).Minimum;$ymax=($ys|Measure-Object -Maximum).Maximum
$scale=[Math]::Min(1400/($xmax-$xmin),1230/($ymax-$ymin))
$tx=800-$scale*($xmin+$xmax)/2;$ty=800-$scale*($ymin+$ymax)/2
$maxDegree=($degrees.Values|Measure-Object -Maximum).Maximum
$minDegree=($degrees.Values|Measure-Object -Minimum).Minimum
$rootElement=$svg.DocumentElement
$rootElement.SetAttribute('viewBox','0 0 1600 1680');$rootElement.SetAttribute('width','1600');$rootElement.SetAttribute('height','1680')
function Element($name,$attributes,$content=''){
 $el=$svg.CreateElement($name,'http://www.w3.org/2000/svg');foreach($key in $attributes.Keys){$el.SetAttribute($key,[string]$attributes[$key])};if($content){$el.InnerText=$content};return ,$el
}
$group=Element 'g' @{transform="translate($(Num $tx) $(Num $ty)) scale($(Num $scale))"}
foreach($path in $paths){$path.SetAttribute('stroke','#82909f');$path.SetAttribute('stroke-opacity','0.25');$path.SetAttribute('stroke-width',(Num (0.55/$scale)));[void]$group.AppendChild($path)}
foreach($c in $circles){
 $id=$c.GetAttribute('class').Substring(3);$t=($degrees[$id]-$minDegree)/[double]($maxDegree-$minDegree)
 $r=1.5+4.5*[Math]::Sqrt($t)
 $red=[int](72-47*$t);$green=[int](143-78*$t);$blue=[int](183-67*$t)
 $c.SetAttribute('fill',('#{0:x2}{1:x2}{2:x2}' -f $red,$green,$blue));$c.SetAttribute('r',(Num ($r/$scale)));$c.SetAttribute('stroke','#ffffff');$c.SetAttribute('stroke-width',(Num (0.35/$scale)));[void]$group.AppendChild($c)
}
while($rootElement.HasChildNodes){[void]$rootElement.RemoveChild($rootElement.FirstChild)}
[void]$rootElement.AppendChild((Element 'rect' @{width='1600';height='1680';fill='white'}))
[void]$rootElement.AppendChild($group)
function Text($x,$y,$size,$content,$fill='#172b40'){
 [void]$rootElement.AppendChild((Element 'text' @{x=(Num $x);y=(Num $y);'font-family'='Arial, sans-serif';'font-size'=$size;fill=$fill} $content))
}
Text 70 67 34 'Western States Power Grid'
Text 70 106 18 'Full undirected network | 4,941 nodes | 6,594 transmission-line edges'
Text 70 137 16 'Yifan Hu layout: positions show connectivity, not geographic location.' '#536579'
$top=@($degrees.Keys | Sort-Object @{Expression={$degrees[$_]};Descending=$true},@{Expression={[int]$_}} | Select-Object -First 6)
$records=@();$i=0
foreach($id in $top){
 $x=$tx+$scale*$positions[$id][0];$y=$ty+$scale*$positions[$id][1]
 $lx=$x+20;$ly=$y-18-($i%2)*16
 if($lx -gt 1370){$lx=$x-145}
 [void]$rootElement.AppendChild((Element 'line' @{x1=(Num $x);y1=(Num $y);x2=(Num $lx);y2=(Num ($ly-5));stroke='#254b69';'stroke-width'='0.8'}))
 $label="ID $id (k=$($degrees[$id]))"
 $el=Element 'text' @{x=(Num $lx);y=(Num $ly);'font-family'='Arial, sans-serif';'font-size'='15';fill='#153f63';stroke='white';'stroke-width'='4';'paint-order'='stroke'} $label
 [void]$rootElement.AppendChild($el);$records+=@{id=$id;degree=$degrees[$id]};$i++
}
Text 70 1480 21 'HOW TO READ THIS NETWORK'
Text 70 1515 17 'Node size and blue intensity encode degree k (number of incident edges).'
foreach($k in @($minDegree,5,10,$maxDegree)|Select-Object -Unique){
 $x=110+($k-$minDegree)/[double]($maxDegree-$minDegree)*560;$r=1.5+4.5*[Math]::Sqrt(($k-$minDegree)/[double]($maxDegree-$minDegree))
 $t=($k-$minDegree)/[double]($maxDegree-$minDegree)
 $legendColor='#{0:x2}{1:x2}{2:x2}' -f [int](72-47*$t),[int](143-78*$t),[int](183-67*$t)
 [void]$rootElement.AppendChild((Element 'circle' @{cx=(Num $x);cy='1550';r=(Num $r);fill=$legendColor}));Text ($x+12) 1556 15 "k=$k"
}
Text 830 1555 16 'Thin gray lines: unweighted transmission links.'
Text 70 1600 16 'Labels identify the six highest-degree nodes; ties are broken by numeric ID.'
Text 70 1630 15 'IDs are source identifiers. Degree does not establish capacity, power flow, or failure criticality.' '#536579'
$output=Join-Path $folder 'power_grid_annotated_draft.svg';$svg.Save($output)
@{nodes=4941;edges=6594;minDegree=$minDegree;maxDegree=$maxDegree;labeledNodes=$records;layout='Existing Gephi Yifan Hu coordinates';radiusMapping='1.5 + 4.5 sqrt((k-kmin)/(kmax-kmin)) pixels';scope='Full analyzed network; no filtering';status='Draft, visual review required'}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $folder 'power_grid_style_audit.json') -Encoding utf8
Write-Output $output
