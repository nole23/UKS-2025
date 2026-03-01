import { Component, EventEmitter, Input, Output } from '@angular/core';
import { TableColumn } from '../interface/table-column';
import { CommonModule, DatePipe } from '@angular/common';

@Component({
  selector: 'app-table-component',
  imports: [DatePipe, CommonModule],
  templateUrl: './table-component.html',
  styleUrl: './table-component.scss',
})
export class TableComponent {
  @Input() columns: TableColumn[] = []
  @Input() data: any[] = []
  @Input() rowAction?: (row:any)=>void;

  @Output() selectionChange = new EventEmitter<any>();

  onSelect(row: any, colKey: string) {
    if (!colKey) return;

    this.data.forEach(r => r[colKey] = false);
    row[colKey] = true;

    this.selectionChange.emit(row);
  }
}
