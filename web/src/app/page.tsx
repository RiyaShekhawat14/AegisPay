import { Badge, Button, Card, DataTable, Input, StatusDot } from "@/components";

export default function Home() {
  return (
    <main className="mx-auto max-w-4xl p-10">
      <div className="mb-6 flex items-center gap-2">
        <StatusDot />
        <h1 className="text-3xl font-bold">AegisPay</h1>
      </div>
      <p className="mb-6 text-muted">
        AI proposes. Only the deterministic AegisPay control plane may authorize and execute
        financial actions.
      </p>

      <div className="grid gap-4">
        <Card title="Control plane" action={<Badge tone="ok">operational</Badge>}>
          <p className="text-sm text-muted">
            Policy, risk, authorization and payment execution all live here.
          </p>
        </Card>

        <Card title="Recent activity">
          <DataTable
            headers={["Event", "Risk", "Status"]}
            rows={[
              [<span>Approval requested</span>, <Badge tone="warn">HIGH</Badge>, <Badge>pending</Badge>],
              [<span>Payment reconciled</span>, <Badge tone="ok">LOW</Badge>, <Badge tone="ok">done</Badge>],
            ]}
          />
        </Card>

        <div className="flex items-end gap-3">
          <Input label="Customer reference" placeholder="cust_123" />
          <Button variant="primary">Create verification</Button>
        </div>
      </div>
    </main>
  );
}
