import { useUIStore } from '../store/uiStore'

export const FontSizeControl = () => {
  const { scale, increase, decrease, reset } = useUIStore()

  return (
    <div className="flex items-center gap-1" title="Adjust text size">
      <button
        onClick={decrease}
        aria-label="Decrease text size"
        className="w-7 h-7 flex items-center justify-center rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors text-sm font-bold disabled:opacity-40"
        disabled={scale <= 1}
      >
        A
      </button>
      <button
        onClick={reset}
        aria-label="Reset text size"
        className="w-7 h-7 flex items-center justify-center rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
        title="Reset to default size"
      >
        <span className="text-xs">↺</span>
      </button>
      <button
        onClick={increase}
        aria-label="Increase text size"
        className="w-7 h-7 flex items-center justify-center rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors text-base font-bold disabled:opacity-40"
        disabled={scale >= 1.5}
      >
        A
      </button>
    </div>
  )
}