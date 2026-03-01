import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-user-profile',
  imports: [],
  templateUrl: './user-profile.html',
  styleUrl: './user-profile.scss',
})
export class UserProfile implements OnInit {
  user: any;

  constructor(private route: ActivatedRoute ) {}

  ngOnInit() {
    const userId = this.route.snapshot.paramMap.get('id');
    // pozovi API da učitaš usera po id
    console.log(userId)
  }
}
