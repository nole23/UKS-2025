import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-modal-dialog-component',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './modal-dialog-component.html',
  styleUrl: './modal-dialog-component.scss',
})
export class ModalDialogComponent {
  @Input() title = 'Info';
  @Input() message = '';
  @Input() type = '';
  @Input() innerDiv = '';
  @Input() isCancelVisibility: boolean = false;
  @Output() ok = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  okClicked() {
    this.ok.emit();
  }

  cancelClicked() {
    this.cancel.emit();
  }
}
