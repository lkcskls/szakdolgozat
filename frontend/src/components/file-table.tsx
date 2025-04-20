"use client"

import {
    ColumnDef,
    flexRender,
    getCoreRowModel,
    useReactTable,
} from "@tanstack/react-table"

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { deleteFileByName, downloadFileByName } from "@/lib/api"
import DeleteFileButton from "./DeleteFileButton"
import { useKey } from "./KeyProvider"

// This type is used to define the shape of our data.
// You can use a Zod schema here if you want.
export type FileTableData = {
    id: string
    filename: string
    encrypted: boolean
    created_at: string
}

export function columns(onDataChanged: () => void): ColumnDef<FileTableData>[] {
    return [
        {
            accessorKey: "filename",
            header: "Filename",
            cell: ({ row }) => {
                const file = row.original
                const { keyHex } = useKey();
                return (
                    <button
                        onClick={() => downloadFileByName(file.filename, keyHex)}
                        className="text-blue-600 hover:underline"
                    >
                        {file.filename}
                    </button>
                )
            },
        },
        {
            accessorKey: "encrypted",
            header: "Encrypted",
            cell: ({ row }) => row.original.encrypted ? "Yes" : "No"
        },
        {
            accessorKey: "created_at",
            header: "Uploaded",
            cell: ({ row }) => {
                const date = new Date(row.original.created_at)
                return date.toLocaleString()  // vagy pl. date-fns-szel formázva
            },
        },
        {
            id: "actions",
            header: "",
            cell: ({ row }) => {
                const file = row.original

                const handleDelete = async () => {
                    try {
                        await deleteFileByName(file.filename)
                        // itt érdemes frissíteni a táblát vagy state-et is, ha kell
                        //alert(`${file.filename} deleted successfully`)
                        onDataChanged();
                    } catch (error) {
                        console.error(error)
                        //alert("Delete failed.")
                    }
                }

                return (
                    <DeleteFileButton onAction={handleDelete} />
                )
            }
        }
    ]
}


interface DataTableProps<TData, TValue> {
    columns: ColumnDef<TData, TValue>[]
    data: TData[]
    onDataChanged: () => void
}

export function DataTable<TData, TValue>({
    columns,
    data,
    onDataChanged
}: DataTableProps<TData, TValue>) {
    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
    })

    return (
        <div className="rounded-md border">
            <Table>
                <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                        <TableRow key={headerGroup.id}>
                            {headerGroup.headers.map((header) => {
                                return (
                                    <TableHead key={header.id}>
                                        {header.isPlaceholder
                                            ? null
                                            : flexRender(
                                                header.column.columnDef.header,
                                                header.getContext()
                                            )}
                                    </TableHead>
                                )
                            })}
                        </TableRow>
                    ))}
                </TableHeader>
                <TableBody>
                    {table.getRowModel().rows?.length ? (
                        table.getRowModel().rows.map((row) => (
                            <TableRow
                                key={row.id}
                                data-state={row.getIsSelected() && "selected"}
                            >
                                {row.getVisibleCells().map((cell) => (
                                    <TableCell key={cell.id}>
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </TableCell>
                                ))}
                            </TableRow>
                        ))
                    ) : (
                        <TableRow>
                            <TableCell colSpan={columns.length} className="h-24 text-center">
                                No results.
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        </div>
    )
}
