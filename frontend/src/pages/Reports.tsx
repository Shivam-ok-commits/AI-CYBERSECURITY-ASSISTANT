import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { Button } from "../components/ui/Button";
import { FileBarChart, FolderOpen } from "lucide-react";
import { useElectron } from "../hooks/useElectron";

export default function Reports() {
  const { isElectron, openInExplorer, api } = useElectron();

  const handleOpenFolder = async () => {
    if (!api) return;
    const reportsPath = await api.app.getPath("userData").then((p: string) => `${p}/reports`);
    openInExplorer(reportsPath);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-text-primary">Reports</h1>
          <p className="text-sm text-text-secondary mt-1">Generate and export security reports</p>
        </div>
        {isElectron && (
          <Button variant="secondary" size="sm" icon={<FolderOpen size={14} />} onClick={handleOpenFolder}>
            Open Reports Folder
          </Button>
        )}
      </div>
      <Card>
        <EmptyState
          icon={<FileBarChart size={48} />}
          title="No reports yet"
          description="Reports will be available soon. You'll be able to generate PDF, HTML, and Markdown exports."
        />
      </Card>
    </div>
  );
}
