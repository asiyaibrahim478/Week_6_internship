import { Injectable, inject } from '@angular/core';
import { AuthService } from './auth.service';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  sources?: string[];
  isStreaming?: boolean;
  timestamp: Date;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private auth = inject(AuthService);
  private apiUrl = 'http://localhost:5000';
  private sessionId = this.getOrCreateSessionId();

  private getOrCreateSessionId(): string {
    let sid = localStorage.getItem('library_chat_session_id');
    if (!sid) {
      sid = 'session_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now();
      localStorage.setItem('library_chat_session_id', sid);
    }
    return sid;
  }

  public getSessionId(): string {
    return this.sessionId;
  }

  public resetSession(): void {
    this.sessionId = 'session_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now();
    localStorage.setItem('library_chat_session_id', this.sessionId);
  }

  /**
   * End-to-End SSE Streaming Consumer (Week 6 Part F)
   * Connects to .NET API proxy (/api/assistant/ask/stream) and receives real-time token chunks.
   */
  async askStream(
    question: string,
    onChunk: (text: string) => void,
    onComplete: () => void,
    onError: (err: any) => void
  ): Promise<void> {
    const token = this.auth.token();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${this.apiUrl}/api/assistant/ask/stream`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          question: question,
          sessionId: this.sessionId
        })
      });

      if (!response.ok) {
        if (response.status === 503) {
          throw new Error('The AI assistant is temporarily unavailable (circuit breaker active). Please try again shortly.');
        }
        throw new Error(`Server returned HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('ReadableStream is not supported or response body is null.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });
        const lines = chunkText.split('\n\n');

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          
          const text = trimmed.substring(5).trim();
          if (text === '[DONE]') {
            onComplete();
            return;
          }
          onChunk(text);
        }
      }
      onComplete();
    } catch (err) {
      onError(err);
    }
  }

  /**
   * Resilient Non-Streaming Fallback Query (Week 6 Part E)
   */
  async ask(question: string): Promise<{ answer: string; sources: string[]; confidence?: string }> {
    const token = this.auth.token();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.apiUrl}/api/assistant/ask`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        question: question,
        sessionId: this.sessionId
      })
    });

    if (!response.ok) {
      if (response.status === 503) {
        throw new Error('The AI assistant is temporarily unavailable. Circuit breaker is active.');
      }
      throw new Error(`HTTP Error: ${response.status}`);
    }

    return await response.json();
  }
}
