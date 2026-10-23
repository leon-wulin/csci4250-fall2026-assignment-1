import fs from 'node:fs';import path from 'node:path';import {createRequire} from 'node:module';
const require=createRequire(path.join(path.resolve(process.argv[2]),'package.json'));
const {PDFDocument,StandardFonts,rgb}=require('pdf-lib');
const dir=path.resolve(import.meta.dirname,'../results/gephi');
const scene=JSON.parse(fs.readFileSync(path.join(dir,'grqc_figure_scene.json'),'utf8').replace(/^\uFEFF/,''));
const W=1600,H=1640;const doc=await PDFDocument.create();const page=doc.addPage([W/2,H/2]);const font=await doc.embedFont(StandardFonts.Helvetica);
const svg=[`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="100%" height="100%" fill="white"/>`];
const col=h=>rgb(...[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255));
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;');
function text(x,y,s,size=22,c='#20384d'){svg.push(`<text x="${x}" y="${y}" font-family="Arial,sans-serif" font-size="${size}" fill="${c}">${esc(s)}</text>`);page.drawText(s,{x:x/2,y:(H-y)/2,size:size/2,font,color:col(c)});}
function line(x1,y1,x2,y2,c,opacity=.2,width=.6){svg.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-opacity="${opacity}" stroke-width="${width}"/>`);page.drawLine({start:{x:x1/2,y:(H-y1)/2},end:{x:x2/2,y:(H-y2)/2},color:col(c),opacity,thickness:width/2});}
function circle(x,y,r,c){svg.push(`<circle cx="${x}" cy="${y}" r="${r}" fill="${c}" stroke="white" stroke-width=".4"/>`);page.drawCircle({x:x/2,y:(H-y)/2,size:r/2,color:col(c),borderWidth:.2,borderColor:rgb(1,1,1)});}
const xs=scene.nodes.map(n=>n.x),ys=scene.nodes.map(n=>n.y);const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
const scale=Math.min(1400/(xmax-xmin),1120/(ymax-ymin));const tx=800-scale*(xmin+xmax)/2,ty=725-scale*(ymin+ymax)/2;
const groups=Object.entries(Object.groupBy(scene.nodes,n=>n.community??'other')).sort((a,b)=>b[1].length-a[1].length);
const palette=['#0072b2','#e69f00','#009e73','#cc79a7','#d55e00','#56b4e9','#756bb1','#8c6d31'];
const colorMap={};groups.filter(([k])=>k!=='other').forEach(([k],i)=>colorMap[k]=palette[i]);
const maxDegree=Math.max(...scene.nodes.map(n=>n.degree));const byId=new Map(scene.nodes.map(n=>[n.id,{...n,px:tx+scale*n.x,py:ty+scale*n.y}]));
text(65,58,'ca-GrQc scientific collaboration network',34);text(65,96,'5,242 authors | 14,484 coauthorship edges | complete analyzed network',22);
text(65,128,'ForceAtlas 2 layout; color identifies selected modularity communities.',21);
for(const e of scene.edges){const s=byId.get(e.source),t=byId.get(e.target);line(s.px,s.py,t.px,t.py,'#88949e',.18,.65);}
for(const n of byId.values())circle(n.px,n.py,1.4+5*Math.sqrt(n.degree/maxDegree),colorMap[n.community]??'#aeb5bb');
const top=[...byId.values()].sort((a,b)=>b.degree-a.degree||Number(a.id)-Number(b.id)).slice(0,6);const boxes=[];
for(const n of top){let x=n.px+20,y=n.py-16;const width=235,height=25;if(x+width>1510)x=n.px-width-15;for(let i=0;i<30&&boxes.some(b=>x<b.x+b.w&&x+width>b.x&&y<b.y+b.h&&y+height>b.y);i++)y+=28;boxes.push({x,y:y-20,w:width,h:height});line(n.px,n.py,x,y-7,'#374c60',.9,.9);svg.push(`<rect x="${x-3}" y="${y-22}" width="${width}" height="27" fill="white" fill-opacity=".9"/>`);page.drawRectangle({x:(x-3)/2,y:(H-y-5)/2,width:width/2,height:13.5,color:rgb(1,1,1),opacity:.9});text(x,y,`ID ${n.id} (k=${n.degree})`,23);}
text(65,1365,'COMMUNITY COLORS',23);const legend=groups.filter(([k])=>k!=='other');legend.push(['other',groups.find(([k])=>k==='other')[1]]);
legend.forEach(([k,nodes],i)=>{const x=75+(i%3)*505,y=1400+Math.floor(i/3)*36;circle(x,y-6,6,colorMap[k]??'#aeb5bb');text(x+17,y,k==='other'?`Other communities (${nodes.length} nodes)`:`Class ${k}: ${nodes.length} nodes`,21);});
for(const [i,k] of [0,10,40,81].entries()){circle(80+i*210,1496,1.4+5*Math.sqrt(k/maxDegree),'#657d90');text(95+i*210,1503,`k=${k}`,20);}
text(65,1535,`Node radius increases with degree k (0-${maxDegree}); lines show coauthorship.`,21);
text(65,1558,'Six highest-degree authors labeled by source ID; IDs are not personal names.',20);
text(65,1590,'Gray combines other communities, not a single group. No nodes or edges filtered.',20);
svg.push('</svg>');fs.writeFileSync(path.join(dir,'grqc_final.svg'),svg.join('\n'));fs.writeFileSync(path.join(dir,'grqc_final.pdf'),await doc.save());
fs.writeFileSync(path.join(dir,'grqc_style_audit.json'),JSON.stringify({nodes:scene.nodes.length,edges:scene.edges.length,maxDegree,top:top.map(n=>({id:n.id,degree:n.degree})),legend:legend.map(([id,n])=>({id,count:n.length,color:colorMap[id]??'#aeb5bb'})),radius:'1.4+5 sqrt(k/kmax)',scale,scope:'full network; frozen GraphML topology verified'},null,2));
await require('sharp')(path.join(dir,'grqc_final.svg')).png().toFile(path.join(dir,'grqc_final.png'));
console.log('Generated SVG, vector PDF, PNG and style audit');
