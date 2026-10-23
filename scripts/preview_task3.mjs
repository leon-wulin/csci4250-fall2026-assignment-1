// Presentation-only preview from frozen empirical frequency tables. No refitting.
import fs from 'node:fs';
import {createRequire} from 'node:module';
const req=createRequire('C:/Users/lin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json');
const {PDFDocument,StandardFonts,rgb}=req('pdf-lib');
const colors=[rgb(0,.4,.7),rgb(.85,.35,0),rgb(0,.6,.4)];
for(const base of ['grqc','power'])for(const metric of ['clustering','component_size']){
 const doc=await PDFDocument.create(),p=doc.addPage([600,310]),font=await doc.embedFont(StandardFonts.Helvetica);
 const text=(s,x,y,size=10,c=rgb(.12,.12,.12))=>p.drawText(s,{x,y,size,font,color:c});
 const line=(x,y,a,b,c=rgb(.8,.8,.8))=>p.drawLine({start:{x,y},end:{x:a,y:b},color:c,thickness:.6});
 const sets=['real','er','ba'].map(id=>fs.readFileSync(`results/distributions/${base}_${id}__${metric}__frequencies.csv`,'utf8').trim().split(/\r?\n/).slice(1).map(r=>r.split(',').map(Number)));
 const component=metric==='component_size';
 const xmax=component?Math.ceil(Math.log10(Math.max(...sets.flat().map(r=>r[0])))):1;
 for(let i=0;i<sets.length;i++)sets[i]=sets[i].filter(r=>Number.isFinite(r[2])&&r[2]>0);
 const ymin=Math.min(-1,Math.floor(Math.log10(Math.min(...sets.flat().map(r=>r[2])))));
 const X=v=>65+465*(component?Math.log10(v)/xmax:v),Y=v=>75+180*(Math.log10(v)-ymin)/(-ymin);
 text(`${base==='grqc'?'ca-GrQc':'Power Grid'}: ${component?'component-size':'local clustering'} distribution`,65,287,14);
 for(let v=ymin;v<=0;v++){const y=Y(10**v);line(65,y,530,y);text(`10^${v}`,24,y-3,9);}
 for(let i=0;i<=5;i++){const val=component?10**(xmax*i/5):i/5;const x=X(val);text(component?Math.round(val).toString():val.toFixed(1),x-7,59,9);}
 line(65,75,65,255,rgb(0,0,0));line(65,75,530,75,rgb(0,0,0));
 text(component?'Component size (nodes; log scale)':'Local clustering coefficient C',175,39,11);text('Empirical probability (log scale)',65,267,10);
 sets.forEach((rows,i)=>{const dx=(i-1)*2.5;for(const [v,,prob] of rows){p.drawCircle({x:X(v)+dx,y:Y(prob),size:3.1,borderColor:colors[i],borderWidth:1,color:rgb(1,1,1)});}
 const label=['Real','ER','BA'][i];text(label,350+i*65,267,10,colors[i]);
 const total=rows.reduce((s,r)=>s+r[1],0),zero=rows.find(r=>r[0]===0)?.[1]??0;
 text(component?`${label}: ${total} component(s)${total===1?`; P(S=${rows[0][0]})=1`:''}`:`${label}: P(C=0)=${(zero/total).toFixed(6)} (${zero}/${total})`,65,20-i*9,8,colors[i]);
 });
 fs.writeFileSync(`results/plots/task3_preview/${base}__${metric}.pdf`,await doc.save());
}
