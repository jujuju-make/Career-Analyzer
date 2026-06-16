"use client";

import { useState, useEffect } from "react";
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

  // 从 localStorage 恢复 taskId（刷新/返回后按钮不消失）
  useEffect(() => {
    const saved = localStorage.getItem("career_task_id");
    if (saved) {
      setTaskId(saved);
      setStep("done");
    }
  }, []);

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

  const [progressMsg, setProgressMsg] = useState("");

  const handleStartAnalysis = async () => {
    if (!resumeId || !targetPosition) return;
    setLoading(true);
    setError(null);
    setProgressMsg("正在解析简历和 JD...");
    try {
      const result = await api.startAnalysis(resumeId, jdInput, targetPosition);
      setTaskId(result.task_id);
      // 持久化到 localStorage
      localStorage.setItem("career_task_id", result.task_id);
      setStep("done");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
      setProgressMsg("");
    }
  };

  const handleNewAnalysis = () => {
    localStorage.removeItem("career_task_id");
    setTaskId(null);
    setResumeFile(null);
    setResumeId(null);
    setJdText("");
    setJdFile(null);
    setJdInput("");
    setTargetPosition("");
    setStep("upload");
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight mb-3 gradient-text">
          AI 职业助手
        </h1>
        <p className="text-muted-foreground text-sm max-w-lg mx-auto">
          上传简历、填写目标岗位和职位描述，AI 将自动分析匹配度、识别技能差距、提供优化建议，并为你准备模拟面试
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-3 mb-8 text-sm">
        {["上传简历", "职位描述", "分析完成"].map((label, i) => {
          const stepMap: Step[] = ["upload", "jd", "analyze"];
          const current = stepMap.indexOf(step);
          const idx = stepMap.indexOf(stepMap[i]);
          return (
            <div key={label} className="flex items-center gap-3">
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
                  idx <= current
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground"
                }`}
              >
                <span
                  className={`inline-block w-4 h-4 rounded-full text-center text-[10px] leading-4 font-bold ${
                    idx < current
                      ? "bg-primary text-primary-foreground"
                      : idx === current
                      ? "bg-primary text-primary-foreground"
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
        <Card className="card-accent card-shadow">
          <CardHeader>
            <CardTitle className="text-base">上传简历</CardTitle>
            <CardDescription>支持 PDF 格式，最大 10MB</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer bg-secondary/30">
              <Input
                type="file"
                accept=".pdf"
                className="hidden"
                id="resume-upload"
                onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
              />
              <label htmlFor="resume-upload" className="cursor-pointer block">
                {resumeFile ? (
                  <span className="text-sm text-foreground font-medium">{resumeFile.name}</span>
                ) : (
                  <>
                    <div className="text-3xl mb-2 opacity-30">📄</div>
                    <span className="text-sm text-muted-foreground">
                      点击选择或拖拽上传简历 PDF
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
              {loading ? "上传中..." : "上传简历"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: JD Input */}
      {step === "jd" && (
        <Card className="card-accent card-shadow">
          <CardHeader>
            <CardTitle className="text-base">职位描述</CardTitle>
            <CardDescription>
              粘贴职位描述文本，或上传截图 / PDF
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block font-medium">
                目标岗位
              </label>
              <Input
                placeholder="例如：软件工程师实习生"
                value={targetPosition}
                onChange={(e) => setTargetPosition(e.target.value)}
              />
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block font-medium">
                JD 文本
              </label>
              <Textarea
                placeholder="在此粘贴职位描述..."
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
              <span className="text-xs text-muted-foreground">或上传图片</span>
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
                {loading ? "..." : "上传图片"}
              </Button>
            </div>

            <Button
              onClick={handleStartAnalysis}
              disabled={!targetPosition || loading}
              className="w-full"
            >
              {loading ? "分析中..." : "开始分析"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Done */}
      {step === "done" && (
        <div className="space-y-6">
          <Card className="card-accent card-shadow">
            <CardHeader>
              <CardTitle className="text-base">分析完成</CardTitle>
              <CardDescription>
                你的简历分析已完成，可以选择查看以下内容
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-lg bg-gradient-to-r from-primary/5 via-primary/5 to-transparent border border-primary/10">
                <div className="flex items-center gap-2 mb-2">
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="font-medium text-sm">任务 ID: {taskId}</span>
                </div>
                <p className="text-muted-foreground text-xs">
                  分析结果已保存，你可以随时返回查看
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Button
                  variant="default"
                  className="h-auto py-4 flex flex-col items-center gap-1"
                  onClick={() => router.push(`/analysis?task_id=${taskId}`)}
                >
                  <span className="text-lg">📊</span>
                  <span className="text-sm font-medium">查看简历分析</span>
                  <span className="text-[10px] text-primary-foreground/70">匹配度、技能差距、风险评估</span>
                </Button>
                <Button
                  variant="secondary"
                  className="h-auto py-4 flex flex-col items-center gap-1"
                  onClick={() => router.push(`/optimization?task_id=${taskId}`)}
                >
                  <span className="text-lg">💡</span>
                  <span className="text-sm font-medium">查看优化建议</span>
                  <span className="text-[10px] text-muted-foreground">简历优化、项目推荐</span>
                </Button>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => router.push(`/interview?task_id=${taskId}`)}
                >
                  🎤 开始模拟面试
                </Button>
                <Button
                  variant="ghost"
                  className="flex-1"
                  onClick={handleNewAnalysis}
                >
                  重新分析
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
