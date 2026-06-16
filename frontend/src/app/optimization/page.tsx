"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api/client";

function OptimizationContent() {
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
    const id = taskIdParam || localStorage.getItem("career_task_id");
    if (id) fetchResult(id);
  }, [taskIdParam]);

  if (!taskIdParam && !localStorage.getItem("career_task_id")) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-12 text-center">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">优化建议</h1>
          <p className="text-muted-foreground text-sm">暂无分析数据，请先上传简历进行分析。</p>
        </div>
        <Button onClick={() => router.push("/")}>去首页分析</Button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight mb-2">优化建议</h1>
        <p className="text-muted-foreground text-sm">
          查看简历优化建议和推荐的学习项目。
        </p>
      </div>

      {loading && (
        <div className="animate-pulse space-y-4">
          <div className="h-48 bg-secondary rounded-lg" />
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
          {/* Resume Optimization */}
          {result.optimition && (
            <Card className="card-accent card-shadow">
              <CardHeader>
                <CardTitle className="text-base">简历优化建议</CardTitle>
                <CardDescription>基于目标岗位的简历修改建议</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200/50 text-sm whitespace-pre-wrap font-mono text-xs leading-relaxed text-foreground">
                  {result.optimition}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Project Recommendations */}
          {result.project_recommendations?.length > 0 && (
            <Card className="card-accent card-shadow">
              <CardHeader>
                <CardTitle className="text-base">推荐项目</CardTitle>
                <CardDescription>GitHub 开源项目，帮助你填补技能差距</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {result.project_recommendations.map((p: any, i: number) => (
                  <div key={i} className="p-4 rounded-lg bg-secondary/50 border border-border/50 hover:border-primary/20 transition-colors">
                    <div className="flex items-start justify-between mb-1">
                      <div>
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium hover:text-primary transition-colors"
                        >
                          {p.name || p.repo}
                        </a>
                        {p.stars && (
                          <span className="text-xs text-muted-foreground ml-2">★ {p.stars}</span>
                        )}
                      </div>
                      {p.language && (
                        <Badge variant="secondary" className="text-[10px]">{p.language}</Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">{p.description}</p>
                    {p.relevance && (
                      <div className="mt-2 text-xs text-primary/70 font-medium">
                        相关度: {p.relevance}
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {!result.optimition && (!result.project_recommendations || result.project_recommendations.length === 0) && (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-sm text-muted-foreground">暂无优化建议数据。</p>
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={() => router.push(`/analysis?task_id=${result.task_id}`)}>
              📊 查看简历分析
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

export default function OptimizationPage() {
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
      <OptimizationContent />
    </Suspense>
  );
}
