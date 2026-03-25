interface Props {
  classes: string[];
  selected: string | null;
  onSelect: (ac: string | null) => void;
}

export default function AssetClassSelector({ classes, selected, onSelect }: Props) {
  return (
    <select
      value={selected || ''}
      onChange={(e) => onSelect(e.target.value || null)}
      className="px-3 py-[5px] text-[12px] font-medium border border-gray-200 rounded bg-white appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='8' height='5' viewBox='0 0 8 5' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l3 3 3-3' stroke='%23999' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'right 8px center',
        paddingRight: '26px',
        minWidth: '120px',
      }}
    >
      <option value="">All Classes</option>
      {classes.map((ac) => (
        <option key={ac} value={ac}>{ac}</option>
      ))}
    </select>
  );
}
