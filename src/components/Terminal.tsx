import React, { useEffect, useImperativeHandle, useRef, forwardRef } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import 'xterm/css/xterm.css';
import '../styles/Terminal.css';

export interface TerminalRef {
    writeln: (text: string) => void;
    clear: () => void;
}

export const Terminal = forwardRef<TerminalRef>((props, ref) => {
    const terminalRef = useRef<HTMLDivElement>(null);
    const xtermRef = useRef<XTerm | null>(null);
    const fitAddonRef = useRef(new FitAddon());
    
    useImperativeHandle(ref, () => ({
        writeln: (text: string) => {
            xtermRef.current?.writeln(text);
        },
        clear: () => {
            xtermRef.current?.clear();
        }
    }));
    
    useEffect(() => {
        if (!terminalRef.current) return;
        
        const xterm = new XTerm({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: {
                background: '#1e1e1e',
                foreground: '#d4d4d4',
                cursor: '#d4d4d4'
            }
        });
        
        xterm.loadAddon(fitAddonRef.current);
        xterm.loadAddon(new WebLinksAddon());
        
        xterm.open(terminalRef.current);
        fitAddonRef.current.fit();
        
        xtermRef.current = xterm;
        
        const handleResize = () => fitAddonRef.current.fit();
        window.addEventListener('resize', handleResize);
        
        return () => {
            window.removeEventListener('resize', handleResize);
            xterm.dispose();
        };
    }, []);
    
    return <div ref={terminalRef} className="terminal-container" />;
}); 