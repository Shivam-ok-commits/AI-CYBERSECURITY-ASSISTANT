import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { FileBarChart } from "lucide-react";

export default function Reports() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Reports</h1>
        <p className="text-sm text-text-secondary mt-1">Generate and export security reports</p>
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
