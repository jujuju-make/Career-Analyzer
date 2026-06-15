"use client";

import { Suspense, useState, useRef, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api/client";

interface Message {
  role: "assistant" | "user" | "system";
  content: string;
  module_label?: string;
  score?: number;
  correct?: string;
}

function InterviewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskIdParam = searchParams.get("task_id");

  const [taskId, setTaskId] = useState(taskIdParam || "");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [interviewOver, setInterviewOver] = useState(false);
  const [finalResult, setFinalResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFollowUp, setIsFollowUp] = useState(false);
  const [followUpQuestion, setFollowUpQuestion] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStart = async () => {
    if (!taskId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.startInterview(taskId);
      setSessionId(result.session_id);
      setTotalQuestions(result.current_question.total);
      setCurrentIndex(result.current_question.question_index);
      setMessages([
        {
          role: "system",
          content: `Mock Interview Started — ${result.current_question.total} questions total.`,
        },
        {
          role: "assistant",
          content: result.current_question.question,
          module_label: result.current_question.module_label,
        },
      ]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!sessionId || !currentAnswer.trim()) return;
    const answer = currentAnswer.trim();
    setCurrentAnswer("");

    setMessages((prev) => [...prev, { role: "user", content: answer }]);

    setLoading(true);
    setError(null);
    try {
      const result = await api.submitAnswer(sessionId, answer);

      setMessages((prev) => [
        ...prev,
        { role: "system", content: result.feedback, score: result.score, correct: result.correct },
      ]);

      if (result.follow_up_question) {
        setFollowUpQuestion(result.follow_up_question);
        setIsFollowUp(true);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: result.follow_up_question!, module_label: "Follow-up" },
        ]);
      } else if (result.next_question) {
        setCurrentIndex(result.next_question.question_index);
        setIsFollowUp(false);
        setFollowUpQuestion(null);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: result.next_question!.question, module_label: result.next_question!.module_label },
        ]);
      } else if (result.interview_over) {
        setInterviewOver(true);
        setFinalResult(result.final_result);
        setMessages((prev) => [
          ...prev,
          { role: "system", content: `Interview Complete! Verdict: ${result.final_result?.verdict?.toUpperCase()} | Score: ${result.final_result?.overall_score}/100` },
        ]);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (!taskIdParam) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">Mock Interview</h1>
          <p className="text-muted-foreground text-sm">Start a mock interview based on your analysis results.</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex gap-3">
              <Input placeholder="Enter Task ID..." value={taskId} onChange={(e) => setTaskId(e.target.value)} />
              <Button onClick={handleStart} disabled={loading || !taskId}>
                {loading ? "Starting..." : "Start Interview"}
              </Button>
            </div>
            {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!sessionId) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">Mock Interview</h1>
          <p className="text-muted-foreground text-sm">Task: {taskIdParam}</p>
        </div>
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Ready to start your mock interview? You'll be asked 14 questions covering project experience, job skills, fundamentals, and behavior.
            </p>
            <Button onClick={handleStart} disabled={loading} size="lg">
              {loading ? "Generating Questions..." : "Begin Interview"}
            </Button>
            {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-semibold tracking-tight">Mock Interview</h1>
          {!interviewOver && <div className="text-xs text-muted-foreground">Question {currentIndex + 1} of {totalQuestions}</div>}
        </div>
        {!interviewOver && (
          <div className="w-full h-1 bg-secondary rounded-full overflow-hidden">
            <div className="h-full bg-foreground/20 rounded-full transition-all duration-300" style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%` }} />
          </div>
        )}
      </div>

      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
            {messages.map((msg, i) => (
              <div key={i}>
                {msg.role === "assistant" && (
                  <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-secondary flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-[10px]">AI</span>
                    </div>
                    <div className="flex-1">
                      {msg.module_label && <Badge variant="secondary" className="text-[10px] mb-1">{msg.module_label}</Badge>}
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                )}
                {msg.role === "user" && (
                  <div className="flex gap-3 justify-end">
                    <div className="max-w-[80%]">
                      <p className="text-sm bg-secondary/50 rounded-lg px-4 py-2.5 whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    <div className="w-6 h-6 rounded-full bg-foreground/10 flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-[10px]">U</span>
                    </div>
                  </div>
                )}
                {msg.role === "system" && (
                  <div className="flex gap-3 pl-9">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {msg.score !== undefined && (
                          <Badge variant={msg.correct === "true" ? "default" : msg.correct === "partial" ? "secondary" : "destructive"} className="text-[10px]">
                            Score: {msg.score}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </CardContent>
      </Card>

      {!interviewOver && (
        <div className="flex gap-3">
          <Textarea
            placeholder={isFollowUp ? "Answer the follow-up question..." : "Type your answer..."}
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmitAnswer(); } }}
            className="min-h-[60px]"
            disabled={loading}
          />
          <Button onClick={handleSubmitAnswer} disabled={loading || !currentAnswer.trim()} className="self-end">
            {loading ? "..." : "Send"}
          </Button>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-destructive">{error}</p>}

      {interviewOver && finalResult && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Interview Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-secondary/30 text-center">
                <div className="text-xs text-muted-foreground mb-1">Verdict</div>
                <Badge variant={finalResult.verdict === "pass" ? "default" : "destructive"} className="text-sm">
                  {finalResult.verdict?.toUpperCase()}
                </Badge>
              </div>
              <div className="p-4 rounded-lg bg-secondary/30 text-center">
                <div className="text-xs text-muted-foreground mb-1">Overall Score</div>
                <div className="text-2xl font-semibold">{finalResult.overall_score}/100</div>
              </div>
            </div>
            {finalResult.module_scores && (
              <div>
                <h3 className="text-sm font-medium mb-2">Module Scores</h3>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(finalResult.module_scores).map(([key, score]) => (
                    <div key={key} className="p-3 rounded-lg bg-secondary/30">
                      <div className="text-xs text-muted-foreground mb-1">{key.replace(/_/g, " ")}</div>
                      <div className="text-lg font-semibold">{String(score)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {finalResult.summary && (
              <div className="p-4 rounded-lg bg-secondary/30">
                <div className="text-xs text-muted-foreground mb-1">Summary</div>
                <p className="text-sm">{finalResult.summary}</p>
              </div>
            )}
            <div className="flex gap-3">
              <Button variant="secondary" className="flex-1" onClick={() => router.push(`/results?task_id=${taskId}`)}>
                View Full Results
              </Button>
              <Button variant="outline" className="flex-1" onClick={() => window.location.reload()}>
                Restart Interview
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function InterviewPage() {
  return (
    <Suspense fallback={
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-secondary rounded" />
          <div className="h-4 w-96 bg-secondary rounded" />
          <div className="h-32 bg-secondary rounded-lg" />
        </div>
      </div>
    }>
      <InterviewContent />
    </Suspense>
  );
}
