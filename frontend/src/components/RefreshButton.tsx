import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"

interface RefreshButtonProps {
    onClick: () => void
    isLoading?: boolean
}

export function RefreshButton({ onClick, isLoading = false }: RefreshButtonProps) {
    return (
        <Button
            variant="outline"
            onClick={onClick}
            disabled={isLoading}
        >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            {isLoading ? "Loading..." : "Refresh"}
        </Button>
    )
}