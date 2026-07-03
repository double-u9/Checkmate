import { Skeleton } from '@/components/ui/Skeleton';

export default function Loading() {
  return (
    <div className="min-h-screen px-4 py-6 sm:px-8 lg:pl-80">
      <div className="mb-8 max-w-3xl space-y-3">
        <Skeleton className="h-3 w-36" />
        <Skeleton className="h-9 w-72" />
        <Skeleton className="h-4 w-full max-w-2xl" />
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <Skeleton className="aspect-square min-h-[320px]" />
        <div className="space-y-4">
          <Skeleton className="h-56" />
          <Skeleton className="h-36" />
        </div>
      </div>
    </div>
  );
}
