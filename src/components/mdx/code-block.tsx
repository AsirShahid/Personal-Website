import { type ComponentProps } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

type CodeBlockProps = ComponentProps<"pre"> & {
  "data-title"?: string;
};

// Rendered statically inside MDX content (no hydration), so the copy
// behavior is wired up by an inline script in the blog post page that
// delegates clicks on [data-copy-button].
export function CodeBlock({ children, ...props }: CodeBlockProps) {
  const title = props["data-title"];

  return (
    <div className="group relative rounded-xl overflow-hidden border border-border my-6">
      {title && (
        <div className="px-4 py-2 text-xs font-medium border-b border-border bg-muted/50 text-foreground">
          {title}
        </div>
      )}
      <button
        type="button"
        data-copy-button
        aria-label="Copy code"
        className={cn(
          "absolute size-8 inline-flex items-center justify-center text-primary cursor-pointer right-3 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity rounded-md border border-border bg-background hover:bg-accent hover:text-accent-foreground",
          title ? "top-13" : "top-3"
        )}
      >
        <Copy data-copy-icon className="size-4" />
        <Check data-copied-icon className="size-4 hidden" />
      </button>
      <pre {...props} className={cn("p-4 m-0! overflow-x-auto text-sm", props.className)}>
        {children}
      </pre>
    </div>
  );
}
