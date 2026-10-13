import { Directory, File, Paths } from 'expo-file-system';
import { QuizDrafts } from './drafts';
import { draftJournal } from './journal';
const root = new Directory(Paths.document, 'swipe-iq-quiz-drafts-v1');
function file(slot:number) { root.create({idempotent:true,intermediates:true}); return new File(root,'answers-'+slot+'.json'); }
export const quizDrafts = new QuizDrafts(draftJournal({
 async read(slot) { const target=file(slot);return target.exists?target.text():null; },
 async write(slot,data) { file(slot).write(data); },
 async clear() { if(root.exists) root.delete(); },
}));
export const clearQuizDrafts = () => quizDrafts.clear();
