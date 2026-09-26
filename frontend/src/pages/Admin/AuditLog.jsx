import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, Page, Spinner } from "../../components/ui";

export default function AuditLog() {
  const [events, setEvents] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.audit().then(setEvents).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorBanner error={error} />;
  if (!events) return <Spinner />;

  return (
    <Page title="Audit Log">
      <Card>
        <table className="w-full">
          <thead>
            <tr>
              <th className="th">Timestamp</th>
              <th className="th">Actor</th>
              <th className="th">Role</th>
              <th className="th">Event</th>
              <th className="th">Entity</th>
              <th className="th">Details</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id}>
                <td className="td whitespace-nowrap text-slate-500">
                  {new Date(e.created_at).toLocaleString()}
                </td>
                <td className="td">{e.actor_id ?? "—"}</td>
                <td className="td">{e.actor_role ? <Badge value={e.actor_role} /> : "—"}</td>
                <td className="td font-medium">{e.event_type}</td>
                <td className="td">
                  {e.entity_type}
                  {e.entity_id ? `#${e.entity_id}` : ""}
                </td>
                <td className="td text-xs text-slate-500">{JSON.stringify(e.details)}</td>
              </tr>
            ))}
            {events.length === 0 && (
              <tr>
                <td className="td text-slate-400" colSpan={6}>
                  No audit events yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}
