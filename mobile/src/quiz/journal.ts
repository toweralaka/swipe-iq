// Two small files: a failed write never replaces the latest complete copy.
export function draftJournal(files:{read:(slot:number)=>Promise<string|null>;write:(slot:number,value:string)=>Promise<void>;clear:()=>Promise<void>}) {
 async function latest(){const raw=await Promise.all([files.read(0),files.read(1)]);const copies=raw.flatMap((value,slot)=>{if(value===null)return [];try{const record=JSON.parse(value);if(!Number.isSafeInteger(record.revision)||record.revision<1||typeof record.data!=='string')return [];JSON.parse(record.data);return [{slot,revision:record.revision,data:record.data}];}catch{return [];}}).sort((a,b)=>b.revision-a.revision);
 if(!copies.length&&raw.some(value=>value!==null))throw new Error('Saved answers could not be read. They have not been removed.');return copies[0]??null;}
 return {async read(){return (await latest())?.data??null;},async write(data:string){const previous=await latest();await files.write(previous?.slot===0?1:0,JSON.stringify({revision:(previous?.revision??0)+1,data}));},clear:files.clear};
}
