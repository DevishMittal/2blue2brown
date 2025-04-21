"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import { Session, Message } from "@/lib/types";
import { supabase } from "@/lib/supabaseClient";

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<string>("Guest User");
  const [sessionsList, setSessionsList] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [messageHistory, setMessageHistory] = useState<Message[]>([]);
  const [newSession, setNewSession] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Bypass authentication and just initialize the app
    setLoading(false);
  }, []);

  if (loading) return <div className="p-4">Loading...</div>;

  return (
    <main className="flex h-screen">
      <Sidebar
        user={user}
        currentSession={currentSession}
        setCurrentSession={setCurrentSession}
        messageHistory={messageHistory}
        setMessageHistory={setMessageHistory}
        sessionsList={sessionsList}
        setSessionsList={setSessionsList}
        newSession={newSession}
        setNewSession={setNewSession}
      />
      <ChatWindow 
        user={user} 
        currentSession={currentSession} 
        setCurrentSession={setCurrentSession} 
        messageHistory={messageHistory}
        setMessageHistory={setMessageHistory}
        newSession={newSession} 
        setNewSession={setNewSession}/>
    </main>
  );
}
