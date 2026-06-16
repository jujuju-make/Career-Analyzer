"use client";

import { Suspense, useState, useRef, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
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
  const [started, setStarted] = useState(false);
  const [restoring, setRestoring] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 如果没有 taskIdParam，尝试从 localStorage 获取
  useEffect(() => {
    if (!taskIdParam) {
      const saved = localStorage.getItem("career_task_id");
      if (saved) setTaskId(saved);
    }
  }, [taskIdParam]);

  // 页面加载时检查是否有未完成的面试会话
  useEffect(() => {
    const savedSessionId = localStorage.getItem("interview_session_id");
    const savedTaskId = localStorage.getItem("interview_task_id");
    const targetTaskId = taskIdParam || taskId;

    if (savedSessionId && savedTaskId === targetTaskId) {
      restoreSession(savedSessionId);
    }
  }, [taskId, taskIdParam]);

  const restoreSession = async (sid: string) => {
    setRestoring(true);
    try {
      const status = await api.getSessionStatus(sid);
      if (status.status === "in_progress") {
        setSessionId(sid);
        setTotalQuestions(status.total);
        // 如果有追问未完成，当前题还没结束，索引回退一题
        // 例如：答完第1题触发追问，total_asked=1，但追问还没答完
        // 此时应该显示"第1题/共14题"而不是"第2题/共14题"
        if (status.is_follow_up) {
          setCurrentIndex(Math.max(0, status.total_asked - 1));
        } else {
          setCurrentIndex(status.total_asked);
        }
        setIsFollowUp(status.is_follow_up);
        setStarted(true);

        // 恢复已答记录（从后端获取完整历史）
        // 由于后端只存了 answers 没有存完整 messages，我们重建消息列表
        const msgs: Message[] = [];
        if (status.current_question) {
          msgs.push({
            role: "assistant",
            content: status.current_question,
            module_label: status.current_module,
          });
        }
        setMessages(msgs);
      } else if (status.status === "completed") {
        // 面试已完成，跳转到结果页
        router.push(`/results?task_id=${status.task_id}`);
        return;
      }
    } catch (e) {
      // 恢复失败，忽略
      console.log("恢复面试会话失败", e);
    } finally {
      setRestoring(false);
    }
  };

  const handleStart = async () => {
    const id = taskIdParam || taskId;
    if (!id) return;
    setLoading(true);
    setError(null);
    setStarted(true);
    try {
      const result = await api.startInterview(id);
      setSessionId(result.session_id);
      setTotalQuestions(result.current_question.total);
      setCurrentIndex(result.current_question.question_index);
      setMessages([
        {
          role: "assistant",
          content: result.current_question.question,
          module_label: result.current_question.module_label,
        },
      ]);
      // 保存 session 到 localStorage
      localStorage.setItem("interview_session_id", result.session_id);
      localStorage.setItem("interview_task_id", id);
    } catch (e: any) {
      setError(e.message);
      setStarted(false);
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

      // 更新进度：如果有 next_question，使用它的 question_index
      // 如果是追问（follow_up_question），进度不变（追问不算新题）
      // 如果是结束（interview_over），进度已到终点
      if (result.next_question) {
        setCurrentIndex(result.next_question.question_index);
        setIsFollowUp(false);
        setFollowUpQuestion(null);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: result.next_question!.question, module_label: result.next_question!.module_label },
        ]);
      } else if (result.follow_up_question) {
        // 追问：进度不变，但更新追问状态
        setFollowUpQuestion(result.follow_up_question);
        setIsFollowUp(true);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: result.follow_up_question!, module_label: "追问" },
        ]);
      } else if (result.interview_over) {
        setInterviewOver(true);
        setFinalResult(result.final_result);
        // 清除 localStorage 中的 session
        localStorage.removeItem("interview_session_id");
        localStorage.removeItem("interview_task_id");
        setMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: `🎉 面试结束！${result.final_result?.verdict === "pass" ? "恭喜通过！" : "需要继续努力！"} 总分: ${result.final_result?.overall_score}/100`,
          },
        ]);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // 没有 task_id 的情况
  if (!taskIdParam && !taskId && !localStorage.getItem("career_task_id")) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12 text-center">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">模拟面试</h1>
          <p className="text-muted-foreground text-sm">请先完成简历分析，然后开始模拟面试。</p>
        </div>
        <Button onClick={() => router.push("/")}>去首页分析</Button>
      </div>
    );
  }

  // 正在恢复会话
  if (restoring) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12 text-center">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">模拟面试</h1>
          <p className="text-muted-foreground text-sm">正在恢复上次的面试进度...</p>
        </div>
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-secondary rounded-lg" />
        </div>
      </div>
    );
  }

  // 未开始面试 - 显示欢迎界面
  if (!started) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">模拟面试</h1>
          <p className="text-muted-foreground text-sm">
            基于你的简历分析结果，AI 将为你生成针对性的面试题目
          </p>
        </div>
        <Card className="card-accent card-shadow">
          <CardContent className="pt-8 pb-8 text-center">
            <div className="text-5xl mb-4">🎤</div>
            <p className="text-sm text-muted-foreground mb-2 max-w-md mx-auto">
              准备好开始面试了吗？你将回答多道涵盖项目经验、岗位技能、基础知识等方面的题目。
            </p>
            <p className="text-xs text-muted-foreground mb-6">
              任务 ID: {taskIdParam || taskId || localStorage.getItem("career_task_id")}
            </p>
            <Button onClick={handleStart} disabled={loading} size="lg" className="px-8">
              {loading ? "正在生成题目..." : "开始面试"}
            </Button>
            {error && <p className="mt-3 text-xs text-destructive">{error}</p>}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-semibold tracking-tight">模拟面试</h1>
          {!interviewOver && (
            <div className="text-xs text-muted-foreground">
              第 {currentIndex + 1} 题 / 共 {totalQuestions} 题
            </div>
          )}
        </div>
        {!interviewOver && (
          <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-300"
              style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%` }}
            />
          </div>
        )}
      </div>

      {/* Chat Messages */}
      <Card className="mb-6 card-shadow">
        <CardContent className="pt-6">
          <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
            {messages.map((msg, i) => (
              <div key={i}>
                {msg.role === "assistant" && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                      <span className="text-[10px] text-white font-medium">AI</span>
                    </div>
                    <div className="flex-1">
                      {msg.module_label && (
                        <Badge variant="secondary" className="text-[10px] mb-1">
                          {msg.module_label}
                        </Badge>
                      )}
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                )}
                {msg.role === "user" && (
                  <div className="flex gap-3 justify-end">
                    <div className="max-w-[80%]">
                      <p className="text-sm bg-primary/5 rounded-lg px-4 py-2.5 whitespace-pre-wrap border border-primary/10">
                        {msg.content}
                      </p>
                    </div>
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-[10px] font-medium">我</span>
                    </div>
                  </div>
                )}
                {msg.role === "system" && (
                  <div className="flex gap-3 pl-11">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {msg.score !== undefined && (
                          <Badge
                            variant={msg.correct === "true" ? "default" : msg.correct === "partial" ? "secondary" : "destructive"}
                            className="text-[10px]"
                          >
                            得分: {msg.score}
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

      {/* Input Area */}
      {!interviewOver && (
        <div className="flex gap-3">
          <Textarea
            placeholder={isFollowUp ? "回答追问..." : "输入你的回答..."}
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmitAnswer();
              }
            }}
            className="min-h-[60px]"
            disabled={loading}
          />
          <Button
            onClick={handleSubmitAnswer}
            disabled={loading || !currentAnswer.trim()}
            className="self-end"
          >
            {loading ? "..." : "发送"}
          </Button>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-destructive">{error}</p>}

      {/* Interview Results */}
      {interviewOver && finalResult && (
        <Card className="mt-6 card-accent card-shadow">
          <CardHeader>
            <CardTitle className="text-base">面试结果</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/10 text-center">
                <div className="text-xs text-muted-foreground mb-1">是否通过</div>
                <Badge
                  variant={finalResult.verdict === "pass" ? "default" : "destructive"}
                  className="text-sm px-3 py-1"
                >
                  {finalResult.verdict === "pass" ? "✅ 通过" : "❌ 未通过"}
                </Badge>
              </div>
              <div className="p-4 rounded-lg bg-gradient-to-br from-accent/5 to-accent/10 border border-accent/10 text-center">
                <div className="text-xs text-muted-foreground mb-1">总分</div>
                <div className="text-2xl font-semibold text-primary">{finalResult.overall_score}/100</div>
              </div>
            </div>

            {finalResult.module_scores && (
              <div>
                <h3 className="text-sm font-medium mb-2">模块得分</h3>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(finalResult.module_scores).map(([key, score]) => (
                    <div key={key} className="p-3 rounded-lg bg-secondary/50 border border-border/50">
                      <div className="text-xs text-muted-foreground mb-1">
                        {key.replace(/_/g, " ")}
                      </div>
                      <div className="text-lg font-semibold">{String(score)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {finalResult.summary && (
              <div className="p-4 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200/50">
                <div className="text-xs text-muted-foreground mb-1 font-medium">评估总结</div>
                <p className="text-sm">{finalResult.summary}</p>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button
                variant="default"
                className="flex-1"
                onClick={() => router.push(`/results?task_id=${taskIdParam || taskId}`)}
              >
                📋 查看完整结果
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => window.location.reload()}
              >
                🔄 重新面试
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
    <Suspense
      fallback={
        <div className="max-w-3xl mx-auto px-6 py-12">
          <div className="animate-pulse space-y-4">
            <div className="h-8 w-48 bg-secondary rounded" />
            <div className="h-4 w-96 bg-secondary rounded" />
            <div className="h-32 bg-secondary rounded-lg" />
          </div>
        </div>
      }
    >
      <InterviewContent />
    </Suspense>
  );
}
