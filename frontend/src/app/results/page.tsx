"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api/client";

function ResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskIdParam = searchParams.get("task_id");

  const [taskId, setTaskId] = useState(taskIdParam || "");
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [interviewResult, setInterviewResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"analysis" | "interview">("analysis");

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
    if (taskIdParam) fetchResults(taskIdParam);
  }, [taskIdParam]);

  const handleSearch = () => {
    if (taskId) fetchResults(taskId);
  };

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

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight mb-2">Results</h1>
        <p className="text-muted-foreground text-sm">View all analysis and interview results.</p>
      </div>

      <Card className="mb-8">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Input placeholder="Enter Task ID..." value={taskId} onChange={(e) => setTaskId(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSearch()} />
            <Button onClick={handleSearch} disabled={loading || !taskId}>
              {loading ? "Loading..." : "Search"}
            </Button>
          </div>
          {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {(analysisResult || interviewResult) && (
        <div className="flex gap-1 mb-6 p-1 rounded-lg bg-secondary/50 w-fit">
          <button onClick={() => setActiveTab("analysis")} className={`px-4 py-1.5 text-sm rounded-md transition-colors ${activeTab === "analysis" ? "bg-background text-foreground font-medium" : "text-muted-foreground hover:text-foreground"}`}>
            Analysis
          </button>
          <button onClick={() => setActiveTab("interview")} className={`px-4 py-1.5 text-sm rounded-md transition-colors ${activeTab === "interview" ? "bg-background text-foreground font-medium" : "text-muted-foreground hover:text-foreground"}`}>
            Interview
          </button>
        </div>
      )}

      {activeTab === "analysis" && analysisResult && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Analysis Overview</CardTitle>
              <CardDescription>Task: {analysisResult.task_id}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-secondary/30">
                  <div className="text-xs text-muted-foreground mb-1">Match Score</div>
                  <div className="text-2xl font-semibold">{gapData?.match_score !== null ? `${gapData?.match_score}/100` : "—"}</div>
                </div>
                <div className="p-4 rounded-lg bg-secondary/30">
                  <div className="text-xs text-muted-foreground mb-1">Verdict</div>
                  <div className="text-sm font-medium">{gapData?.overall_verdict || "—"}</div>
                </div>
                <div className="p-4 rounded-lg bg-secondary/30">
                  <div className="text-xs text-muted-foreground mb-1">Interview</div>
                  <Badge variant={gapData?.interview_recommendation?.verdict === "yes" ? "default" : gapData?.interview_recommendation?.verdict === "maybe" ? "secondary" : "destructive"}>
                    {gapData?.interview_recommendation?.verdict || "—"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {gapData && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Skill Gap Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {gapData.critical_gaps?.trainable_gaps?.map((g: any, i: number) => (
                  <div key={i} className="p-3 rounded-lg bg-secondary/30">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{g.skill}</span>
                      <Badge variant={g.risk_level === "高" ? "destructive" : "secondary"} className="text-[10px]">{g.risk_level}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">{g.current_level} → {g.required_level}</div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {analysisResult.optimition && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Resume Optimization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-lg bg-secondary/30 text-sm whitespace-pre-wrap font-mono text-xs leading-relaxed">{analysisResult.optimition}</div>
              </CardContent>
            </Card>
          )}

          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={() => router.push(`/interview?task_id=${analysisResult.task_id}`)}>
              Start Mock Interview
            </Button>
            <Button variant="outline" className="flex-1" onClick={() => router.push("/")}>
              New Analysis
            </Button>
          </div>
        </div>
      )}

      {activeTab === "interview" && interviewResult && (
        <div className="space-y-6">
          {interviewResult.rounds?.map((round: any, i: number) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base capitalize">{round.round_name.replace(/_/g, " ")}</CardTitle>
                  <Badge variant={round.verdict === "pass" ? "default" : "destructive"}>{round.verdict}</Badge>
                </div>
                {round.score && <CardDescription>Score: {round.score}/100</CardDescription>}
              </CardHeader>
              {round.summary && (
                <CardContent>
                  <p className="text-sm text-muted-foreground">{round.summary}</p>
                </CardContent>
              )}
            </Card>
          ))}
          {(!interviewResult.rounds || interviewResult.rounds.length === 0) && (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-sm text-muted-foreground">No interview results yet. Start a mock interview first.</p>
                <Button variant="secondary" className="mt-4" onClick={() => router.push(`/interview?task_id=${taskId}`)}>
                  Start Interview
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {!analysisResult && !interviewResult && !loading && !error && (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-muted-foreground">Enter a Task ID to view results.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ResultsPage() {
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
      <ResultsContent />
    </Suspense>
  );
}
