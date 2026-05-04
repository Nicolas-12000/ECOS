"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { MessageSquare, Send, X, Bot, User, Loader2 } from "lucide-react"
import { Button } from "./ui/Button"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/Card"
import { cn } from "@/lib/utils"
import { chat } from "@/lib/api"

export function ChatAssistant() {
  const [isOpen, setIsOpen] = React.useState(false)
  const [messages, setMessages] = React.useState([
    { role: 'bot', content: 'Hola, soy el asistente de ECOS. ¿En qué puedo ayudarte hoy con el análisis epidemiológico?' }
  ])
  const [input, setInput] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)
  const scrollAnchor = React.useRef<HTMLDivElement>(null)
  const scrollContainerRef = React.useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: "smooth"
      })
    }
  }

  React.useEffect(() => {
    // Scroll immediately on message changes
    scrollToBottom();
    
    // Also set a timeout for when the open animation finishes or new content loads
    if (isOpen) {
      const timer = setTimeout(scrollToBottom, 300);
      return () => clearTimeout(timer);
    }
  }, [messages, isOpen, isLoading])

  React.useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener('open-chat', handleOpen);
    return () => window.removeEventListener('open-chat', handleOpen);
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return
    
    const userMsg = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const data = await chat(input)
      setMessages(prev => [...prev, { 
        role: 'bot', 
        content: data.answer 
      }])
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'bot', 
        content: 'Lo siento, hubo un error al procesar tu solicitud. Por favor intenta de nuevo.' 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <div className="fixed bottom-8 right-8 z-50 flex items-center gap-4">
        {!isOpen && (
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-accent text-primary-contrast px-4 py-2 rounded-full shadow-lg text-sm font-bold flex items-center gap-2 cursor-pointer"
            onClick={() => setIsOpen(true)}
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
            </span>
            ✨ Habla con ECOS
          </motion.div>
        )}
        <Button
          onClick={() => setIsOpen(!isOpen)}
          size="icon"
          className="h-16 w-16 rounded-full shadow-[0_0_25px_rgba(22,114,90,0.5)] bg-primary text-primary-contrast hover:scale-110 transition-transform"
        >
          {isOpen ? <X size={28} /> : <MessageSquare size={28} />}
        </Button>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed bottom-24 right-8 z-50 w-[400px] max-w-[calc(100vw-2rem)]"
          >
            <Card className="border-none shadow-2xl overflow-hidden flex flex-col h-[500px]">
              <CardHeader className="bg-primary text-primary-contrast p-4 flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                  <div className="bg-accent rounded-full p-2">
                    <Bot size={20} />
                  </div>
                  <div>
                    <CardTitle className="text-sm font-bold text-white">ECOS AI Assistant</CardTitle>
                    <p className="text-[10px] opacity-70">Basado en RAG & Datos Nacionales</p>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent 
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto p-4 space-y-4"
              >
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={cn(
                      "flex gap-3 max-w-[85%]",
                      msg.role === 'user' ? "ml-auto flex-row-reverse" : ""
                    )}
                  >
                    <div className={cn(
                      "rounded-2xl p-3 text-sm",
                      msg.role === 'user' 
                        ? "bg-accent text-primary-contrast rounded-tr-none" 
                        : "bg-background-soft text-foreground rounded-tl-none"
                    )}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="bg-background-soft rounded-2xl p-3 rounded-tl-none">
                      <Loader2 className="h-4 w-4 animate-spin text-accent" />
                    </div>
                  </div>
                )}
                <div ref={scrollAnchor} />
              </CardContent>

              <div className="p-4 border-t border-border bg-surface">
                <form 
                  onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                  className="flex gap-2"
                >
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Escribe tu consulta..."
                    className="flex-1 bg-background-soft border-none rounded-full px-4 py-2 text-sm focus:ring-1 focus:ring-accent outline-none"
                  />
                  <Button type="submit" size="icon" className="h-9 w-9">
                    <Send size={16} />
                  </Button>
                </form>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
