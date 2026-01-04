// Required for static export - returns empty array since debates are loaded dynamically
export function generateStaticParams() {
  return [];
}

export default function DebateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
