"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api/client";

type Step = "upload" | "jd" | "analyze" | "done";

export default function Home() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("upload");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Resume
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);

  // JD
  const [jdText, setJdText] = useState("");
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [jdInput, setJdInput] = useState("");

  // Position
  const [targetPosition, setTargetPosition] = useState("");

  // Result
  const [taskId, setTaskId] = useState<string | null>(null);

  const handleUploadResume = async () => {
    if (!resumeFile) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.uploadResume(resumeFile);
      setResumeId(result.resume_id);
      setStep("jd");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadJd = async () => {
    if (jdFile) {
      setLoading(true);
      setError(null);
      try {
        const result = await api.uploadJdImage(jdFile);
        setJdInput(result.text);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleStartAnalysis = async () => {
    if (!resumeId || !targetPosition) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.startAnalysis(resumeId, jdInput, targetPosition);
      setTaskId(result.task_id);
      // 自动跳转到 Dashboard
      router.push(`/dashboard?task_id=${result.task_id}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-2xl font-semibold tracking-tight mb-2">
          AI Career Copilot
        </h1>
        <p className="text-muted-foreground text-sm">
          Upload your resume, paste a job description, and let AI analyze your fit,
          identify skill gaps, and prepare you for interviews.
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-3 mb-8 text-sm">
        {["Upload Resume", "Job Description", "Analysis"].map((label, i) => {
          const stepMap: Step[] = ["upload", "jd", "analyze"];
          const current = stepMap.indexOf(step);
          const idx = stepMap.indexOf(stepMap[i]);
          return (
            <div key={label} className="flex items-center gap-3">
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
                  idx <= current
                    ? "bg-secondary text-secondary-foreground"
                    : "text-muted-foreground"
                }`}
              >
                <span
                  className={`inline-block w-4 h-4 rounded-full text-center text-[10px] leading-4 font-bold ${
                    idx < current
                      ? "bg-primary text-primary-foreground"
                      : idx === current
                      ? "bg-foreground text-background"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {i + 1}
                </span>
                {label}
              </div>
              {i < 2 && <Separator className="w-8" />}
            </div>
          );
        })}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
          {error}
        </div>
      )}

      {/* Step 1: Upload Resume */}
      {step === "upload" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Upload Resume</CardTitle>
            <CardDescription>PDF format, max 10MB</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-muted-foreground/50 transition-colors cursor-pointer">
              <Input
                type="file"
                accept=".pdf"
                className="hidden"
                id="resume-upload"
                onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
              />
              <label htmlFor="resume-upload" className="cursor-pointer block">
                {resumeFile ? (
                  <span className="text-sm text-foreground">{resumeFile.name}</span>
                ) : (
                  <>
                    <div className="text-2xl mb-2 opacity-30">◇</div>
                    <span className="text-sm text-muted-foreground">
                      Click to select or drag and drop your resume PDF
                    </span>
                  </>
                )}
              </label>
            </div>
            <Button
              onClick={handleUploadResume}
              disabled={!resumeFile || loading}
              className="w-full"
            >
              {loading ? "Uploading..." : "Upload Resume"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: JD Input */}
      {step === "jd" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Job Description</CardTitle>
            <CardDescription>
              Paste the JD text or upload a screenshot / PDF
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block">
                Target Position
              </label>
              <Input
                placeholder="e.g. Software Engineer Intern"
                value={targetPosition}
                onChange={(e) => setTargetPosition(e.target.value)}
              />
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block">
                JD Text
              </label>
              <Textarea
                placeholder="Paste the job description here..."
                className="min-h-[200px]"
                value={jdText}
                onChange={(e) => {
                  setJdText(e.target.value);
                  setJdInput(e.target.value);
                }}
              />
            </div>

            <div className="flex items-center gap-3">
              <Separator className="flex-1" />
              <span className="text-xs text-muted-foreground">or upload</span>
              <Separator className="flex-1" />
            </div>

            <div className="flex gap-3">
              <div className="flex-1">
                <Input
                  type="file"
                  accept="image/*"
                  className="text-xs"
                  onChange={(e) => setJdFile(e.target.files?.[0] || null)}
                />
              </div>
              <Button
                variant="secondary"
                onClick={handleUploadJd}
                disabled={!jdFile || loading}
                size="sm"
              >
                {loading ? "..." : "Upload Image"}
              </Button>
            </div>

            <Button
              onClick={handleStartAnalysis}
              disabled={!targetPosition || loading}
              className="w-full"
            >
              {loading ? "Analyzing..." : "Start Analysis"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Done */}
      {step === "done" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Analysis Started</CardTitle>
            <CardDescription>
              Your analysis is being processed. This may take a minute.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-secondary/50 text-sm">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="font-medium">Task ID: {taskId}</span>
              </div>
              <p className="text-muted-foreground text-xs">
                The analysis is running in the background. You can check the results
                on the Dashboard page.
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="secondary"
                className="flex-1"
                onClick={() => router.push(`/results?task_id=${taskId}`)}
              >
                View Results
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => router.push("/dashboard")}
              >
                Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
