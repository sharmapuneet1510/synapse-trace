interface Props {
  logic: string | null | undefined;
  file: string | null | undefined;
  line: number | null | undefined;
}

export default function XsltLogicBlock({ logic, file, line }: Props) {
  const fileName = file?.split('/').pop() || '';
  const locationLabel = fileName + (line ? `:${line}` : '');

  return (
    <div className="glass-card">
      <div className="section-bar" style={{ borderRadius: '12px 12px 0 0' }}>
        <svg fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
        </svg>
        <span>XSLT Logic</span>
        {locationLabel && (
          <span className="text-[10px] font-normal opacity-60 ml-1 normal-case">({locationLabel})</span>
        )}
      </div>

      <div className="bg-[#0f172a] p-5 overflow-x-auto">
        <pre className="text-[11.5px] leading-[1.8] text-emerald-400 font-mono m-0">
          <code>{logic || '// No XSLT logic found for this field'}</code>
        </pre>
      </div>
    </div>
  );
}
