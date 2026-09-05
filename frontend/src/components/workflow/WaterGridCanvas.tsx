import React, { useEffect, useRef } from 'react';

interface WaterGridCanvasProps {
  activeAgent?: string;
  isStreaming?: boolean;
  className?: string;
}

export default function WaterGridCanvas({ activeAgent, isStreaming, className = '' }: WaterGridCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let ripples: { x: number; y: number; r: number; maxR: number; alpha: number; color: string }[] = [];

    const handleResize = () => {
      canvas.width = canvas.parentElement?.clientWidth || window.innerWidth;
      canvas.height = canvas.parentElement?.clientHeight || window.innerHeight;
    };
    handleResize();
    window.addEventListener('resize', handleResize);

    // Color mapper for agents
    const getAgentColor = (agent?: string) => {
      switch (agent) {
        case 'finance': return '#00F0FF';
        case 'risk': return '#FF3366';
        case 'growth': return '#00FF9D';
        case 'recovery': return '#FFB800';
        case 'supervisor': return '#A855F7';
        default: return '#00F0FF';
      }
    };

    // Trigger ripple when streaming or active agent changes
    const addRipple = (x: number, y: number, color: string) => {
      ripples.push({
        x,
        y,
        r: 5,
        maxR: 120,
        alpha: 0.6,
        color
      });
    };

    let interval: any;
    if (isStreaming) {
      interval = setInterval(() => {
        if (canvas) {
          const cx = canvas.width / 2 + (Math.random() - 0.5) * 200;
          const cy = canvas.height * 0.35 + (Math.random() - 0.5) * 150;
          addRipple(cx, cy, getAgentColor(activeAgent));
        }
      }, 1200);
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Render ripples
      for (let i = ripples.length - 1; i >= 0; i--) {
        const rp = ripples[i];
        ctx.beginPath();
        ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI * 2);
        ctx.strokeStyle = rp.color;
        ctx.globalAlpha = rp.alpha;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Increment size & fade out
        rp.r += 0.8;
        rp.alpha = Math.max(0, 0.6 * (1 - rp.r / rp.maxR));

        if (rp.r >= rp.maxR || rp.alpha <= 0) {
          ripples.splice(i, 1);
        }
      }
      ctx.globalAlpha = 1;

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      if (interval) clearInterval(interval);
    };
  }, [activeAgent, isStreaming]);

  return (
    <canvas 
      ref={canvasRef} 
      className={`absolute inset-0 pointer-events-none z-0 ${className}`} 
      aria-hidden="true"
    />
  );
}
