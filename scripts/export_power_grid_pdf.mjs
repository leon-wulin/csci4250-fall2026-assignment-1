// Render the known SVG subset produced by style_power_grid_svg.ps1 as vector PDF.
// Dependencies are resolved from CODEX_NODE_MODULES or a supplied module root.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(path.join(process.argv[2] || process.env.CODEX_NODE_MODULES || process.cwd(),'package.json'));
const {PDFDocument,StandardFonts,rgb}=require('pdf-lib');
const root=path.resolve(import.meta.dirname,'..');
const dir=path.join(root,'results/gephi');
const svg=fs.readFileSync(path.join(dir,'power_grid_annotated_draft.svg'),'utf8');
const attrs=s=>Object.fromEntries([...s.matchAll(/([\w:-]+)="([^"]*)"/g)].map(m=>[m[1],m[2]]));
const doc=await PDFDocument.create();
const page=doc.addPage([800,780]);
const font=await doc.embedFont(StandardFonts.Helvetica);
const color=s=>{const h=s.replace('#','');return rgb(...[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)/255));};
const group=svg.match(/<g\b([^>]*)>([\s\S]*?)<\/g>/);
const tr=attrs(group[1]).transform.match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/).slice(1).map(Number);
const point=(x,y)=>({x:(tr[0]+tr[2]*x)/2,y:780-(tr[1]+tr[2]*y-150)/2});
let edgeCount=0,nodeCount=0;
for(const m of group[2].matchAll(/<path\b([^>]*)\/?\s*>/g)){
 const a=attrs(m[1]);const q=a.d.match(/M\s*([-\d.eE]+),([-\d.eE]+)\s*L\s*([-\d.eE]+),([-\d.eE]+)/);
 if(!q)throw Error('Unsupported path');const v=q.slice(1).map(Number);
 page.drawLine({start:point(v[0],v[1]),end:point(v[2],v[3]),thickness:Number(a['stroke-width'])*tr[2]/2,color:color(a.stroke),opacity:Number(a['stroke-opacity'])});edgeCount++;
}
for(const m of group[2].matchAll(/<circle\b([^>]*)\/?\s*>/g)){
 const a=attrs(m[1]);page.drawCircle({...point(Number(a.cx),Number(a.cy)),size:Number(a.r)*tr[2]/2,color:color(a.fill),borderColor:rgb(1,1,1),borderWidth:0.175});nodeCount++;
}
// Selected-node callouts, excluding poster title and footer.
const outside=svg.slice(svg.indexOf('</g>')+4);
for(const m of outside.matchAll(/<line\b([^>]*)\/?\s*>/g)){
 const a=attrs(m[1]);page.drawLine({start:{x:Number(a.x1)/2,y:780-(Number(a.y1)-150)/2},end:{x:Number(a.x2)/2,y:780-(Number(a.y2)-150)/2},thickness:0.4,color:color(a.stroke)});
}
for(const m of outside.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/g)){
 const a=attrs(m[1]);if(!m[2].startsWith('ID '))continue;
 const x=Number(a.x)/2,y=780-(Number(a.y)-150)/2;
 const w=font.widthOfTextAtSize(m[2],11);
 page.drawRectangle({x:x-2,y:y-2,width:w+4,height:13,color:rgb(1,1,1),opacity:0.88});
 page.drawText(m[2],{x,y,size:11,font,color:color(a.fill)});
}
page.drawText('Degree k: node size and blue intensity increase with incident-edge count.',{x:35,y:46,size:11,font,color:rgb(.09,.18,.26)});
for(const [i,k] of [1,5,10,19].entries()){
 const t=(k-1)/18;page.drawCircle({x:55+i*105,y:25,size:(1.5+4.5*Math.sqrt(t))/2,color:rgb((72-47*t)/255,(143-78*t)/255,(183-67*t)/255)});
 page.drawText(`k=${k}`,{x:65+i*105,y:21,size:10,font,color:rgb(.09,.18,.26)});
}
page.drawText('Gray edges: transmission links',{x:485,y:21,size:10,font,color:rgb(.25,.3,.35)});
if(nodeCount!==4941||edgeCount!==6594)throw Error('PDF topology count mismatch');
doc.setTitle('Western States Power Grid: degree-encoded network');
doc.setCreator('Gephi layout; reproducible PowerShell/Node vector styling');
fs.writeFileSync(path.join(dir,'power_grid_final.pdf'),await doc.save());
fs.copyFileSync(path.join(dir,'power_grid_annotated_draft.svg'),path.join(dir,'power_grid_final.svg'));
console.log(JSON.stringify({nodeCount,edgeCount,pdf:'power_grid_final.pdf'}));
