import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { RepositoryDetails } from './repository-details';
import { ProjectService } from '../../services/project';
import { UserService } from '../../services/user';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';

describe('RepositoryDetails', () => {
  let component: RepositoryDetails;
  let fixture: ComponentFixture<RepositoryDetails>;
  let mockProjectService: any;
  let mockUserService: any;

  beforeEach(async () => {
    mockProjectService = {
      getProjectTags: jasmine.createSpy('getProjectTags').and.returnValue(of([
        { id: 1, name: 'v1', updated_at: '2026-01-26T22:19:42.347695Z' },
        { id: 2, name: 'v2', updated_at: '2026-01-27T12:00:00.000000Z' }
      ])),
      getCollaborators: jasmine.createSpy('getCollaborators').and.returnValue(of([
        { id: 1, username: 'user1' },
        { id: 2, username: 'user2' }
      ])),
      addCollaborator: jasmine.createSpy('addCollaborator').and.returnValue(of({})),
      removeCollaborators: jasmine.createSpy('removeCollaborators').and.returnValue(of({})),
      addTag: jasmine.createSpy('addTag').and.returnValue(of({ id: 3, name: 'v3', updated_at: new Date().toISOString() })),
      removeTag: jasmine.createSpy('removeTag').and.returnValue(of({}))
    };

    mockUserService = {
      filterUserByText: jasmine.createSpy('filterUserByText').and.returnValue(of([
        { id: 1, username: 'novica' }
      ]))
    };

    await TestBed.configureTestingModule({
      imports: [
        RepositoryDetails, // standalone komponenta ide u imports
        FormsModule,
      ],
      providers: [
        { provide: ProjectService, useValue: mockProjectService },
        { provide: UserService, useValue: mockUserService },
        DatePipe
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RepositoryDetails);
    component = fixture.componentInstance;
    component.repository = { id: 123 };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load tags and set lastTag', () => {
    component.loadTags();
    expect(component.tags.length).toBe(2);
    expect(component.lastTag.name).toBe('v2'); // najnoviji po updated_at
  });

  it('should load collaborators', () => {
    component.loadCollaborators();
    expect(component.collaborators.length).toBe(2);
  });

  it('should generate random string of correct length', () => {
    const str = component.generateRandomString(5);
    expect(str.length).toBe(5);
  });

  it('should generate random number between 1 and 200 with 2 decimals', () => {
    const num = component['getRandomNumber']();
    expect(num).toBeGreaterThanOrEqual(1);
    expect(num).toBeLessThanOrEqual(200);
    expect(num.toString().split('.')[1].length).toBeLessThanOrEqual(2);
  });

  it('should add tag to top of tags array', () => {
    component.tags = [];
    component.addTag();
    expect(mockProjectService.addTag).toHaveBeenCalled();
    expect(component.tags[0].id).toBe(3);
  });

  it('should remove tag from tags array', () => {
    component.tags = [{ id: 1 }, { id: 2 }];
    component.removeTag({ id: 1 });
    expect(mockProjectService.removeTag).toHaveBeenCalledWith(123, 1);
    expect(component.tags.length).toBe(1);
    expect(component.tags[0].id).toBe(2);
  });

  it('should filter users on searchTerm', fakeAsync(() => {
    component.searchTerm = 'no';
    component.onSearchUser();
    tick();
    expect(mockUserService.filterUserByText).toHaveBeenCalledWith('no');
    expect(component.filteredUsers.length).toBe(1);
    expect(component.filteredUsers[0].username).toBe('novica');
  }));

  it('should select user and clear filteredUsers', () => {
    const user = { id: 1, username: 'novica' };
    component.filteredUsers = [user];
    component.selectUser(user);
    expect(component.selectedUser).toBe(user);
    expect(component.filteredUsers.length).toBe(0);
  });

  it('should add collaborator to top of collaborators', () => {
    component.collaborators = [];
    component.selectedUser = { id: 1, username: 'novica' };
    component.addCollaborator();
    expect(mockProjectService.addCollaborator).toHaveBeenCalledWith(123, 1);
    expect(component.collaborators[0].username).toBe('novica');
  });

  it('should remove collaborator from array', () => {
    component.collaborators = [{ id: 1, username: 'novica' }];
    component.removeCollaborators({ id: 1 });
    expect(mockProjectService.removeCollaborators).toHaveBeenCalledWith(123, 1);
    expect(component.collaborators.length).toBe(0);
  });
});
