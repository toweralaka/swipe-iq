export type LikeState = { liked:boolean|null; busy:boolean; error:string; uncertain:boolean };
export function likeFrom(value:unknown):boolean{if(!value||typeof value!=='object'||!('liked' in value)||typeof value.liked!=='boolean')throw new Error('Could not confirm your like. Tap Retry.');return value.liked;}
export class LikeController {
 private state:LikeState={liked:null,busy:false,error:'',uncertain:false};private listeners=new Set<()=>void>();
 private path:string;private request:(path:string,body?:unknown)=>Promise<unknown>;
 constructor(path:string,request:(path:string,body?:unknown)=>Promise<unknown>){this.path=path;this.request=request;}
 getSnapshot=()=>this.state;
 subscribe=(listener:()=>void)=>{this.listeners.add(listener);return()=>{this.listeners.delete(listener);};};
 private update(values:Partial<LikeState>){this.state={...this.state,...values};for(const listener of this.listeners)listener();}
 async load(){if(this.state.busy)return;this.update({busy:true,error:''});try{this.update({liked:likeFrom(await this.request(this.path)),uncertain:false});}catch{this.update({error:'Could not check your like. Tap Retry.',uncertain:true});}finally{this.update({busy:false});}}
 async change(){if(this.state.busy||this.state.liked===null||this.state.uncertain)return;const desired=!this.state.liked;this.update({busy:true,error:''});try{const liked=likeFrom(await this.request(this.path,{liked:desired}));if(liked!==desired)throw new Error('Unexpected like state');this.update({liked,uncertain:false});}catch{this.update({error:'Could not confirm the change. Tap Retry to check.',uncertain:true});}finally{this.update({busy:false});}}
}
