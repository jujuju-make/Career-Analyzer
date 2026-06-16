"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api/client";

function AnalysisContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskIdParam = searchParams.get("task_id");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchResult = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAnalysisResult(id);
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 优先从 URL 参数获取，否则从 localStorage 获取
    const id = taskIdParam || localStorage.getItem("career_task_id");
    if (id) fetchResult(id);
  }, [taskIdParam]);

  // gap_analysis 已经是解析后的对象（后端已处理）
  const gapData = result?.gap_analysis || null;

  const matchScore = gapData?.match_score ?? null;
  const verdict = gapData?.overall_verdict ?? "";
  const interviewRec = gapData?.interview_recommendation ?? {};

  if (!taskIdParam && !localStorage.getItem("career_task_id")) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-12 text-center">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">简历分析</h1>
          <p className="text-muted-foreground text-sm">暂无分析数据，请先上传简历进行分析。</p>
        </div>
        <Button onClick={() => router.push("/")}>去首页分析</Button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight mb-2">简历分析</h1>
        <p className="text-muted-foreground text-sm">
          查看简历与目标岗位的匹配度、技能差距分析和风险评估。
        </p>
      </div>

      {loading && (
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-secondary rounded-lg" />
          <div className="h-64 bg-secondary rounded-lg" />
        </div>
      )}

      {error && (
        <Card className="mb-6">
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-destructive mb-2">{error}</p>
            <p className="text-xs text-muted-foreground">分析可能还在进行中，请稍后再试。</p>
          </CardContent>
        </Card>
      )}

      {result && (
        <div className="space-y-6">
          {/* Overview */}
          <Card className="card-accent card-shadow">
            <CardHeader>
              <CardTitle className="text-base">分析概览</CardTitle>
              <CardDescription>任务 ID: {result.task_id}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/10">
                  <div className="text-xs text-muted-foreground mb-1">匹配分数</div>
                  <div className="text-2xl font-semibold text-primary">
                    {matchScore !== null ? `${matchScore}/100` : "—"}
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-gradient-to-br from-accent/5 to-accent/10 border border-accent/10">
                  <div className="text-xs text-muted-foreground mb-1">综合评估</div>
                  <div className="text-sm font-medium">{verdict || "—"}</div>
                </div>
                <div className="p-4 rounded-lg bg-gradient-to-br from-chart-2/5 to-chart-2/10 border border-chart-2/10">
                  <div className="text-xs text-muted-foreground mb-1">面试建议</div>
                  <Badge
                    variant={
                      interviewRec.verdict === "yes"
                        ? "default"
                        : interviewRec.verdict === "maybe"
                        ? "secondary"
                        : interviewRec.verdict
                        ? "destructive"
                        : "outline"
                    }
                  >
                    {interviewRec.verdict === "yes" ? "推荐面试" : interviewRec.verdict === "maybe" ? "可考虑" : interviewRec.verdict ? "暂不推荐" : "暂无数据"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Gap Analysis */}
          {gapData && (
            <Card className="card-accent card-shadow">
              <CardHeader>
                <CardTitle className="text-base">技能差距分析</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 结构化数据（新格式） */}
                {gapData.critical_gaps && (gapData.critical_gaps.non_negotiable_misses?.length > 0 || gapData.critical_gaps.trainable_gaps?.length > 0) && (
                  <div>
                    <h3 className="text-sm font-medium mb-2 text-destructive">关键差距</h3>
                    {gapData.critical_gaps.non_negotiable_misses?.length > 0 && (
                      <div className="mb-2">
                        <div className="text-xs text-muted-foreground mb-1">硬性要求不满足：</div>
                        {gapData.critical_gaps.non_negotiable_misses.map((g: string, i: number) => (
                          <div key={i} className="text-sm text-destructive flex items-center gap-2 mb-1">
                            <span className="w-1 h-1 rounded-full bg-destructive shrink-0" />
                            {g}
                          </div>
                        ))}
                      </div>
                    )}
                    {gapData.critical_gaps.trainable_gaps?.map((g: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-secondary/50 mb-2 border border-border/50">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{g.skill}</span>
                          <Badge variant={g.risk_level === "高" ? "destructive" : "secondary"} className="text-[10px]">
                            {g.risk_level}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          当前水平: {g.current_level} → 要求水平: {g.required_level}
                        </div>
                        {g.catch_up_time && (
                          <div className="text-xs text-muted-foreground mt-1">预计追赶时间: {g.catch_up_time}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {gapData.strengths?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-2 text-emerald-600">优势亮点</h3>
                    {gapData.strengths.map((s: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10 mb-2">
                        <div className="text-sm font-medium mb-1 text-emerald-700">{s.strength}</div>
                        <div className="text-xs text-muted-foreground">{s.evidence}</div>
                      </div>
                    ))}
                  </div>
                )}

                {gapData.red_flags?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-2 text-destructive">风险信号</h3>
                    {gapData.red_flags.map((f: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-destructive/5 border border-destructive/10 mb-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{f.flag}</span>
                          <Badge variant="destructive" className="text-[10px]">{f.severity}</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">{f.evidence}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 旧格式兼容：没有结构化数据时显示原始文本 */}
                {(!gapData.critical_gaps || (gapData.critical_gaps.non_negotiable_misses?.length === 0 && gapData.critical_gaps.trainable_gaps?.length === 0)) &&
                 gapData.strengths?.length === 0 &&
                 gapData.red_flags?.length === 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-2 text-destructive">评估详情</h3>
                    <div className="p-4 rounded-lg bg-secondary/30 border border-border/50">
                      <pre className="text-sm whitespace-pre-wrap font-sans text-muted-foreground leading-relaxed">
                        {gapData._raw_text || gapData.honest_assessment || "暂无详细评估数据"}
                      </pre>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={() => router.push(`/optimization?task_id=${result.task_id}`)}>
              💡 查看优化建议
            </Button>
            <Button variant="outline" className="flex-1" onClick={() => router.push(`/interview?task_id=${result.task_id}`)}>
              🎤 开始模拟面试
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={
      <div className="max-w-5xl mx-auto px-6 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-secondary rounded" />
          <div className="h-4 w-96 bg-secondary rounded" />
          <div className="h-32 bg-secondary rounded-lg" />
        </div>
      </div>
    }>
      <AnalysisContent />
    </Suspense>
  );
}
