import { Routes } from '@angular/router';
import { BookListComponent } from './book-list/book-list.component';
import { BookFormComponent } from './book-form/book-form.component';
import { LoginComponent } from './components/login/login.component';
import { AssistantComponent } from './components/assistant/assistant.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'books', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'books', component: BookListComponent },
  { path: 'assistant', component: AssistantComponent },
  { path: 'add-book', component: BookFormComponent, canActivate: [authGuard] },
  { path: 'edit-book/:id', component: BookFormComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'books' }
];
