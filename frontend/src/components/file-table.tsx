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

export type FileTableData = {
    id: string
    filename: string
    encrypted: boolean
    created_at: string
}

const DownloadButton = ({ file }: { file: FileTableData }) => {
    const { keyHex } = useKey();

    return (
        <button
            onClick={() => {
                try {
                    downloadFileByName(file.filename, keyHex)
                }
                catch (err) { console.log(err) }
            }}
            className="text-blue-600 hover:underline"
        >
            {file.filename}
        </button>
    )
}

const DeleteButton = ({ file, onDataChanged }: { file: FileTableData, onDataChanged: () => void }) => {
    const { keyHex } = useKey();

    const handleDelete = async () => {
        try {
            await deleteFileByName(file.filename, keyHex)
            onDataChanged();
        } catch (error) {
            console.log(error)
        }
    }

    return (
        <DeleteFileButton onAction={handleDelete} />
    )
}

export function columns(onDataChanged: () => void): ColumnDef<FileTableData>[] {
    return [
        {
            accessorKey: "filename",
            header: "Filename",
            cell: ({ row }) => {
                const file = row.original
                return (
                    <DownloadButton file={file} />
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
                return date.toLocaleString()
            },
        },
        {
            id: "actions",
            header: "",
            cell: ({ row }) => {
                const file = row.original

                return (
                    <DeleteButton file={file} onDataChanged={onDataChanged} />
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
                                You have no files uploaded
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        </div>
    )
}
