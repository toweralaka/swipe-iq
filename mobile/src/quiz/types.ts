export type Choice = 'a' | 'b' | 'c' | 'd';
export type Question = { id: number; position: number; prompt: string; choices: Record<Choice,string> };
export type Quiz = { version: number; title: string; submission_id: string; questions: Question[] };
export type Attempt = { id: string; version: number; context: { title: string; topic: string; subject: string; examination: string; unit_key: string }; number: number; is_first: boolean; score: number; total: number; completed_at: string };
export type Result = Attempt & { results: { question_id: number; position: number; prompt: string; choices: Record<Choice,string>; selected_choice: Choice; correct_choice: Choice; is_correct: boolean; explanation: string }[] };
export type Progress = { completed_units: number; total_attempts: number; first_attempt_percentage: number | null };
export const uuid = (value: unknown): value is string => typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
function obj(value: unknown): Record<string,unknown> { if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Could not read quiz data. Try again.'); return value as Record<string,unknown>; }
function text(value: unknown): string { if(typeof value !== 'string') throw new Error('Missing quiz text.'); return value; }
function integer(value: unknown, min = 0): number { if(typeof value !== 'number' || !Number.isSafeInteger(value) || value < min) throw new Error('Invalid quiz number.'); return value; }
export function choice(value: unknown): Choice { if(!['a','b','c','d'].includes(String(value))) throw new Error('Choose one of the four answers.'); return value as Choice; }
function choices(value: unknown): Record<Choice,string> { const v=obj(value); return { a:text(v.a),b:text(v.b),c:text(v.c),d:text(v.d) }; }
export function quizFrom(value: unknown): Quiz {
 const v=obj(value); if(!uuid(v.submission_id) || !Array.isArray(v.questions) || v.questions.length !== 3) throw new Error('This quiz could not be opened.');
 const questions=v.questions.map((item,i)=>{ const q=obj(item); if(q.position!==i+1) throw new Error('Quiz questions are out of order.'); return {id:integer(q.id,1),position:integer(q.position,1),prompt:text(q.prompt),choices:choices(q.choices)}; });
 if(new Set(questions.map(q=>q.id)).size!==3) throw new Error('Quiz questions are repeated.');
 return {version:integer(v.version,1),title:text(v.title),submission_id:v.submission_id,questions};
}
export function attemptFrom(value: unknown): Attempt {
 const v=obj(value), c=obj(v.context); if(!uuid(v.id) || typeof v.is_first!=='boolean' || !Number.isFinite(Date.parse(String(v.completed_at)))) throw new Error('Could not read this attempt.');
 const score=integer(v.score); if(v.total!==3 || score>3) throw new Error('Invalid score.');
 return {id:v.id,version:integer(v.version,1),context:{title:text(c.title),topic:text(c.topic),subject:text(c.subject),examination:text(c.examination),unit_key:text(c.unit_key)},number:integer(v.number,1),is_first:v.is_first,score,total:3,completed_at:text(v.completed_at)};
}
export function resultFrom(value: unknown): Result {
 const v=obj(value); if(!Array.isArray(v.results)||v.results.length!==3) throw new Error('Could not read answer explanations.');
 const results=v.results.map(item=>{const q=obj(item); if(typeof q.is_correct!=='boolean') throw new Error('Invalid answer result.'); return {question_id:integer(q.question_id,1),position:integer(q.position,1),prompt:text(q.prompt),choices:choices(q.choices),selected_choice:choice(q.selected_choice),correct_choice:choice(q.correct_choice),is_correct:q.is_correct,explanation:text(q.explanation)};});
 return {...attemptFrom(v),results};
}
export function progressFrom(value: unknown): Progress {
 const v=obj(value); if(v.first_attempt_percentage!==null && (typeof v.first_attempt_percentage!=='number'||!Number.isFinite(v.first_attempt_percentage)||v.first_attempt_percentage<0||v.first_attempt_percentage>100)) throw new Error('Could not read progress.');
 return {completed_units:integer(v.completed_units),total_attempts:integer(v.total_attempts),first_attempt_percentage:v.first_attempt_percentage as number|null};
}
