"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api/client";

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskIdParam = searchParams.get("task_id");

  const [taskId, setTaskId] = useState(taskIdParam || "");
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

  const handleSearch = () => {
    if (taskId) fetchResult(taskId);
  };

  // 如果 URL 带了 task_id，自动加载
  useEffect(() => {
    if (taskIdParam) fetchResult(taskIdParam);
  }, [taskIdParam]);

  // Parse gap_analysis JSON
  const gapData = (() => {
    if (!result?.gap_analysis) return null;
    try {
      return typeof result.gap_analysis === "string"
        ? JSON.parse(result.gap_analysis)
        : result.gap_analysis;
    } catch {
      return null;
    }
  })();

  const matchScore = gapData?.match_score ?? null;
  const verdict = gapData?.overall_verdict ?? "";
  const interviewRec = gapData?.interview_recommendation ?? {};

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight mb-2">Dashboard</h1>
        <p className="text-muted-foreground text-sm">
          View analysis results, skill gap reports, and recommendations.
        </p>
      </div>

      {/* Search */}
      <Card className="mb-8">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Input
              placeholder="Enter Task ID to view results..."
              value={taskId}
              onChange={(e) => setTaskId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={loading || !taskId}>
              {loading ? "Loading..." : "Search"}
            </Button>
          </div>
          {error && (
            <p className="mt-2 text-xs text-destructive">{error}</p>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Analysis Overview</CardTitle>
              <CardDescription>Task: {result.task_id}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-secondary/30">
                  <div className="text-xs text-muted-foreground mb-1">Match Score</div>
                  <div className="text-2xl font-semibold">
                    {matchScore !== null ? `${matchScore}/100` : "—"}
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-secondary/30">
                  <div className="text-xs text-muted-foreground mb-1">Verdict</div>
                  <div className="text-sm font-medium">{verdict || "—"}</div>
                </div>
                <div className="p-4 rounded-lg bg-secondary/30">
                  <div className="text-xs text-muted-foreground mb-1">Interview</div>
                  <Badge
                    variant={
                      interviewRec.verdict === "yes"
                        ? "default"
                        : interviewRec.verdict === "maybe"
                        ? "secondary"
                        : "destructive"
                    }
                  >
                    {interviewRec.verdict || "—"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Gap Analysis */}
          {gapData && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Skill Gap Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {gapData.critical_gaps && (
                  <div>
                    <h3 className="text-sm font-medium mb-2">Critical Gaps</h3>
                    {gapData.critical_gaps.non_negotiable_misses?.length > 0 && (
                      <div className="mb-2">
                        <div className="text-xs text-muted-foreground mb-1">Non-negotiable:</div>
                        {gapData.critical_gaps.non_negotiable_misses.map((g: string, i: number) => (
                          <div key={i} className="text-sm text-destructive flex items-center gap-2 mb-1">
                            <span className="w-1 h-1 rounded-full bg-destructive shrink-0" />
                            {g}
                          </div>
                        ))}
                      </div>
                    )}
                    {gapData.critical_gaps.trainable_gaps?.map((g: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-secondary/30 mb-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{g.skill}</span>
                          <Badge variant={g.risk_level === "高" ? "destructive" : "secondary"} className="text-[10px]">
                            {g.risk_level}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Current: {g.current_level} → Required: {g.required_level}
                        </div>
                        {g.catch_up_time && (
                          <div className="text-xs text-muted-foreground mt-1">Catch-up: {g.catch_up_time}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {gapData.strengths?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-2">Strengths</h3>
                    {gapData.strengths.map((s: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10 mb-2">
                        <div className="text-sm font-medium mb-1">{s.strength}</div>
                        <div className="text-xs text-muted-foreground">{s.evidence}</div>
                      </div>
                    ))}
                  </div>
                )}
                {gapData.red_flags?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-2">Red Flags</h3>
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
              </CardContent>
            </Card>
          )}

          {/* Resume Optimization */}
          {result.optimition && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Resume Optimization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-lg bg-secondary/30 text-sm whitespace-pre-wrap font-mono text-xs leading-relaxed">
                  {result.optimition}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Project Recommendations */}
          {result.project_recommendations?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Project Recommendations</CardTitle>
                <CardDescription>GitHub projects to help fill skill gaps</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {result.project_recommendations.map((p: any, i: number) => (
                  <div key={i} className="p-4 rounded-lg bg-secondary/30">
                    <div className="flex items-start justify-between mb-1">
                      <div>
                        <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium hover:underline">
                          {p.name || p.repo}
                        </a>
                        {p.stars && <span className="text-xs text-muted-foreground ml-2">★ {p.stars}</span>}
                      </div>
                      {p.language && <Badge variant="secondary" className="text-[10px]">{p.language}</Badge>}
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">{p.description}</p>
                    {p.relevance && <div className="mt-2 text-xs text-muted-foreground">Relevance: {p.relevance}</div>}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={() => router.push(`/interview?task_id=${result.task_id}`)}>
              Start Mock Interview
            </Button>
            <Button variant="outline" className="flex-1" onClick={() => window.location.href = "/"}>
              New Analysis
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
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
      <DashboardContent />
    </Suspense>
  );
}
