import { useState, useEffect, useCallback, useRef } from 'react';

export interface WorkflowEvent {
  event_type: string;
  workflow_id: string;
  agent?: string;
  message: string;
  data: Record<string, any>;
  timestamp: string;
}

export function useWorkflowStream(workflowId: string | null) {
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!workflowId) {
      setEvents([]);
      setIsStreaming(false);
      setIsCompleted(false);
      return;
    }

    setEvents([]);
    setIsStreaming(true);
    setIsCompleted(false);
    setError(null);

    const token = localStorage.getItem('token');
    const url = `/api/v1/workflows/${workflowId}/events${token ? `?token=${encodeURIComponent(token)}` : ''}`;

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data);
        if (parsed.event_type === 'stream_closed') {
          setIsStreaming(false);
          setIsCompleted(true);
          es.close();
          return;
        }

        const newEvent: WorkflowEvent = {
          event_type: parsed.event_type,
          workflow_id: parsed.workflow_id || workflowId,
          agent: parsed.agent || 'supervisor',
          message: parsed.message || '',
          data: parsed.data || {},
          timestamp: parsed.timestamp || new Date().toISOString()
        };

        setEvents((prev) => [...prev, newEvent]);

        if (parsed.event_type === 'workflow_completed' || parsed.event_type === 'workflow_failed') {
          setIsStreaming(false);
          setIsCompleted(true);
          es.close();
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };

    es.onerror = (err) => {
      console.warn('SSE connection ended or interrupted:', err);
      setIsStreaming(false);
      es.close();
    };

    return () => {
      es.close();
    };
  }, [workflowId]);

  return { events, isStreaming, isCompleted, error };
}
