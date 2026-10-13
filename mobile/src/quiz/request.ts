export async function forCandidate<T>(candidateId:number|undefined,credential:string,readAccount:()=>Promise<string|null>,send:()=>Promise<T>):Promise<T>{
 const raw=await readAccount();let account:{binding?:string;candidate?:{id?:number};expiresAt?:number}|null=null;try{account=raw?JSON.parse(raw):null;}catch{/* Reject a damaged snapshot. */}
 if(!candidateId||account?.binding!==credential||account?.candidate?.id!==candidateId||typeof account.expiresAt!=='number'||account.expiresAt<=Date.now())throw new Error('The signed-in account changed. Reopen this page.');
 return send();
}
