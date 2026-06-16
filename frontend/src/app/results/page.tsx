"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api/client";

function ResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskIdParam = searchParams.get("task_id");

  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [interviewResult, setInterviewResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"analysis" | "interview">("interview");

  const fetchResults = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const [analysis, interview] = await Promise.all([
        api.getAnalysisResult(id).catch(() => null),
        api.getInterviewResult(id).catch(() => null),
      ]);
      if (analysis) setAnalysisResult(analysis);
      if (interview) setInterviewResult(interview);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const id = taskIdParam || localStorage.getItem("career_task_id");
    if (id) fetchResults(id);
  }, [taskIdParam]);

  const gapData = (() => {
    if (!analysisResult?.gap_analysis) return null;
    try {
      return typeof analysisResult.gap_analysis === "string"
        ? JSON.parse(analysisResult.gap_analysis)
        : analysisResult.gap_analysis;
    } catch {
      return null;
    }
  })();

  const taskId = taskIdParam || localStorage.getItem("career_task_id");

  if (!taskId) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-12 text-center">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">结果</h1>
          <p className="text-muted-foreground text-sm">暂无数据，请先完成简历分析或模拟面试。</p>
        </div>
        <Button onClick={() => router.push("/")}>去首页分析</Button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight mb-2">结果</h1>
        <p className="text-muted-foreground text-sm">查看分析和面试的完整结果。</p>
      </div>

      {loading && (
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-secondary rounded-lg" />
          <div className="h-48 bg-secondary rounded-lg" />
        </div>
      )}

      {error && (
        <Card className="mb-6">
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-destructive mb-2">{error}</p>
            <p className="text-xs text-muted-foreground">数据可能还在处理中，请稍后再试。</p>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      {(analysisResult || interviewResult) && (
        <div className="flex gap-1 mb-6 p-1 rounded-lg bg-secondary/50 w-fit">
          <button
            onClick={() => setActiveTab("interview")}
            className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
              activeTab === "interview"
                ? "bg-white text-foreground font-medium shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            🎤 面试结果
          </button>
          <button
            onClick={() => setActiveTab("analysis")}
            className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
              activeTab === "analysis"
                ? "bg-white text-foreground font-medium shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            📊 分析结果
          </button>
        </div>
      )}

      {/* Interview Results Tab */}
      {activeTab === "interview" && (
        <div className="space-y-6">
          {interviewResult ? (
            interviewResult.rounds?.map((round: any, i: number) => (
              <Card key={i} className="card-accent card-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base capitalize">
                      {round.round_name.replace(/_/g, " ")}
                    </CardTitle>
                    <Badge
                      variant={round.verdict === "pass" ? "default" : "destructive"}
                      className="text-sm px-3 py-1"
                    >
                      {round.verdict === "pass" ? "✅ 通过" : "❌ 未通过"}
                    </Badge>
                  </div>
                  {round.score && (
                    <CardDescription>
                      得分: <span className="font-semibold text-foreground">{round.score}/100</span>
                    </CardDescription>
                  )}
                </CardHeader>
                {round.summary && (
                  <CardContent>
                    <div className="p-3 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200/50">
                      <div className="text-xs text-muted-foreground mb-1 font-medium">评估总结</div>
                      <p className="text-sm">{round.summary}</p>
                    </div>
                  </CardContent>
                )}
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-sm text-muted-foreground mb-4">暂无面试结果，请先完成模拟面试。</p>
                <Button
                  variant="secondary"
                  onClick={() => router.push(`/interview?task_id=${taskId}`)}
                >
                  🎤 开始面试
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Analysis Results Tab */}
      {activeTab === "analysis" && (
        <div className="space-y-6">
          {analysisResult ? (
            <>
              <Card className="card-accent card-shadow">
                <CardHeader>
                  <CardTitle className="text-base">分析概览</CardTitle>
                  <CardDescription>任务 ID: {analysisResult.task_id}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/10">
                      <div className="text-xs text-muted-foreground mb-1">匹配分数</div>
                      <div className="text-2xl font-semibold text-primary">
                        {gapData?.match_score !== null ? `${gapData?.match_score}/100` : "—"}
                      </div>
                    </div>
                    <div className="p-4 rounded-lg bg-gradient-to-br from-accent/5 to-accent/10 border border-accent/10">
                      <div className="text-xs text-muted-foreground mb-1">综合评估</div>
                      <div className="text-sm font-medium">{gapData?.overall_verdict || "—"}</div>
                    </div>
                    <div className="p-4 rounded-lg bg-gradient-to-br from-chart-2/5 to-chart-2/10 border border-chart-2/10">
                      <div className="text-xs text-muted-foreground mb-1">面试建议</div>
                      <Badge
                        variant={
                          gapData?.interview_recommendation?.verdict === "yes"
                            ? "default"
                            : gapData?.interview_recommendation?.verdict === "maybe"
                            ? "secondary"
                            : "destructive"
                        }
                      >
                        {gapData?.interview_recommendation?.verdict === "yes"
                          ? "推荐面试"
                          : gapData?.interview_recommendation?.verdict === "maybe"
                          ? "可考虑"
                          : "暂不推荐"}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {gapData && (
                <Card className="card-accent card-shadow">
                  <CardHeader>
                    <CardTitle className="text-base">技能差距分析</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {gapData.critical_gaps?.trainable_gaps?.map((g: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-secondary/50 border border-border/50">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{g.skill}</span>
                          <Badge
                            variant={g.risk_level === "高" ? "destructive" : "secondary"}
                            className="text-[10px]"
                          >
                            {g.risk_level}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {g.current_level} → {g.required_level}
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {analysisResult.optimition && (
                <Card className="card-accent card-shadow">
                  <CardHeader>
                    <CardTitle className="text-base">简历优化建议</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="p-4 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200/50 text-sm whitespace-pre-wrap font-mono text-xs leading-relaxed">
                      {analysisResult.optimition}
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className="flex gap-3">
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={() => router.push(`/interview?task_id=${analysisResult.task_id}`)}
                >
                  🎤 开始模拟面试
                </Button>
                <Button variant="outline" className="flex-1" onClick={() => router.push("/")}>
                  新建分析
                </Button>
              </div>
            </>
          ) : (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-sm text-muted-foreground">暂无分析结果。</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {!analysisResult && !interviewResult && !loading && !error && (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-muted-foreground">加载中...</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-5xl mx-auto px-6 py-12">
          <div className="animate-pulse space-y-4">
            <div className="h-8 w-48 bg-secondary rounded" />
            <div className="h-4 w-96 bg-secondary rounded" />
            <div className="h-32 bg-secondary rounded-lg" />
          </div>
        </div>
      }
    >
      <ResultsContent />
    </Suspense>
  );
}
