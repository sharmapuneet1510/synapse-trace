interface Props {
  types: string[];
  selected: string | null;
  onSelect: (type: string) => void;
}

export default function ConfigTypeTabs({ types, selected, onSelect }: Props) {
  return (
    <div className="flex gap-1.5">
      {types.map((t) => (
        <button
          key={t}
          onClick={() => onSelect(t)}
          className="flex-1 px-3 py-[6px] rounded-lg text-[11px] font-semibold transition-all duration-150"
          style={{
            background: selected === t
              ? 'linear-gradient(135deg, #dc2626, #b91c1c)'
              : '#f3f4f6',
            color: selected === t ? '#fff' : '#6b7280',
            boxShadow: selected === t ? '0 2px 6px rgba(220,38,38,0.25)' : 'none',
            transform: selected === t ? 'translateY(-1px)' : 'none',
          }}
        >
          {t}
        </button>
      ))}
    </div>
  );
}
