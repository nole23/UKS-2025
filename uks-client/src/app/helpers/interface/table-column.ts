export interface TableButton {
  icon: string;
  title: string;
  class: string;
  fn: (row: any) => void;
}

export interface TableColumn {
  key: string
  label: string
  type?: 'text' | 'date' | 'badge' | 'buttons' | 'radio'
  format?: (value:any,row:any)=>string
  classFn?: (value:any,row:any)=>string
  rowAction?: (row:any)=>void;
  // samo za type='buttons'
  buttons?: TableButton[];
}