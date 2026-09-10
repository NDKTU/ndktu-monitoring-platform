import { ZoomIn } from 'lucide-react'
import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

type PhotoPreviewProps = {
  src: string
  /** Names the shot in the lightbox header, e.g. "Kirish". */
  label: string
  /** Extra context under the title — usually the time the shot was taken. */
  caption?: string | null
  className?: string
}

/**
 * A camera shot small enough to sit in a table cell, opened at full size on
 * click. The thumbnail alone is far too small to recognise a face, so it is a
 * button rather than a plain img: the whole point is getting to the big one.
 */
export function PhotoPreview({
  src,
  label,
  caption,
  className,
}: PhotoPreviewProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={caption ? `${label} — ${caption}` : label}
        title={caption ? `${label} — ${caption}` : label}
        className={cn(
          'group relative size-11 shrink-0 cursor-pointer overflow-hidden rounded-md border border-border/60 transition-colors hover:border-border focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background focus-visible:outline-none',
          className
        )}
      >
        <img
          src={src}
          alt=""
          loading="lazy"
          className="size-full object-cover transition-transform duration-200 group-hover:scale-110"
        />
        <span className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-visible:opacity-100">
          <ZoomIn className="size-4 text-white" aria-hidden />
        </span>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-3xl">
          <DialogHeader className="px-5 pt-5 pb-3">
            <DialogTitle className="text-base">{label}</DialogTitle>
            {caption ? (
              <DialogDescription className="tabular-nums">
                {caption}
              </DialogDescription>
            ) : (
              <DialogDescription className="sr-only">
                Kameradan olingan surat
              </DialogDescription>
            )}
          </DialogHeader>
          <img
            src={src}
            alt={caption ? `${label} — ${caption}` : label}
            className="max-h-[75vh] w-full bg-black object-contain"
          />
        </DialogContent>
      </Dialog>
    </>
  )
}
