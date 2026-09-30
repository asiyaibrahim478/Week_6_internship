import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatMessage } from '../../services/chat.service';

@Component({
  selector: 'app-assistant',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './assistant.component.html',
  styleUrls: ['./assistant.component.css']
})
export class AssistantComponent {
  private chatService = inject(ChatService);

  messages = signal<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your Library Knowledge Assistant powered by LangChain & .NET RAG. Ask me anything about our book catalog, genre recommendations, or real-time borrowing availability!',
      sources: ['Library Catalog'],
      timestamp: new Date()
    }
  ]);

  userInput = signal<string>('');
  isLoading = signal<boolean>(false);
  errorMessage = signal<string | null>(null);
  sessionId = signal<string>(this.chatService.getSessionId());

  // Suggested prompt chips
  suggestedQuestions = [
    'Which books are science fiction in our library?',
    'What book covers database storage engines, replication, and Kafka?',
    'Is book 4 (Dune) available to borrow right now?',
    'What does Clean Code teach about functions?'
  ];

  selectSuggestion(question: string) {
    this.userInput.set(question);
    this.sendMessage();
  }

  resetChat() {
    this.chatService.resetSession();
    this.sessionId.set(this.chatService.getSessionId());
    this.messages.set([
      {
        id: 'welcome-reset',
        sender: 'assistant',
        text: 'Session reset. Started a fresh conversation context!',
        timestamp: new Date()
      }
    ]);
    this.errorMessage.set(null);
  }

  async sendMessage() {
    const query = this.userInput().trim();
    if (!query || this.isLoading()) return;

    this.errorMessage.set(null);
    this.userInput.set('');
    this.isLoading.set(true);

    // 1. Append User Message
    const userMsg: ChatMessage = {
      id: 'user_' + Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date()
    };
    this.messages.update(msgs => [...msgs, userMsg]);

    // 2. Prepare Placeholder Assistant Message for Streaming Tokens
    const assistantMsgId = 'asst_' + Date.now();
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      sender: 'assistant',
      text: '',
      isStreaming: true,
      timestamp: new Date()
    };
    this.messages.update(msgs => [...msgs, assistantMsg]);

    // 3. Stream from .NET Proxy
    await this.chatService.askStream(
      query,
      (chunk: string) => {
        // On token chunk received
        this.messages.update(msgs =>
          msgs.map(m => (m.id === assistantMsgId ? { ...m, text: m.text + chunk } : m))
        );
      },
      () => {
        // On complete
        this.isLoading.set(false);
        this.messages.update(msgs =>
          msgs.map(m => (m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
        );
      },
      (err: any) => {
        // On failure / circuit breaker
        this.isLoading.set(false);
        const errMsg = err?.message || 'Failed to connect to AI Assistant.';
        this.errorMessage.set(errMsg);
        this.messages.update(msgs =>
          msgs.map(m =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  text: m.text || '⚠️ The AI Assistant is temporarily unavailable. (Circuit breaker active)',
                  isStreaming: false
                }
              : m
          )
        );
      }
    );
  }
}
