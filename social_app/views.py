from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import LikePost, Profile, Post, FollowerCounts
from django.contrib.auth.decorators import login_required
from itertools import chain
import random

# Create your views here.

@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    user_following_list = []
    feed = []

    user_following = FollowerCounts.objects.filter(follower=request.user.username)

    for users in user_following:
        user_following_list.append(users.user)
    
    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    #User Suggestions
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)

    new_suggestions_list = [x for x in list(all_users) if (x not in user_following_all)]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if (x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []

    for users in final_suggestions_list:
        username_profile.append(users.id)

    for ids in username_profile:
        profile_list = Profile.objects.filter(userid = ids)
        username_profile_list.append(profile_list)

    suggestions_username_profile_list = list(chain(*username_profile_list))

    context = {
        'user_profile': user_profile,
        'posts':feed_list,
        'suggestions_username_profile_list': suggestions_username_profile_list[:3],
        'user_following': user_following,
    }
    return render(request, 'index.html', context)

@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for user in username_object:
            username_profile.append(user.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(userid=ids)
            username_profile_list.append(profile_lists)

        username_profile_list = list(chain(*username_profile_list))
        
        context = {
            'user_profile': user_profile,
            'username_object': username_object,
            'username_profile_list': username_profile_list,
        }

    return render(request, 'search.html', context)


@login_required(login_url='signin')
def upload(request):

    if request.method=='POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect('/')
    else:
        return redirect('/')


@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    posts = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        posts.no_of_likes = posts.no_of_likes + 1
        posts.save()
        return redirect('/')
    else:
        like_filter.delete()
        posts.no_of_likes = posts.no_of_likes - 1
        posts.save()
        return redirect('/')


@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)
    
    follower = request.user.username
    user = pk

    if FollowerCounts.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_followers = len(FollowerCounts.objects.filter(user=pk))
    user_following = len(FollowerCounts.objects.filter(follower=pk))


    context = {
        'user_object':user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if FollowerCounts.objects.filter(follower=follower, user=user).first():
            delete_follwer = FollowerCounts.objects.get(follower=follower, user=user)
            delete_follwer.delete()
            return redirect('/profile/'+user)
        else:
            new_follower = FollowerCounts.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user)
    
    else:
        return redirect('/')


@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method=='POST':
        
        if request.FILES.get('image') == None:
            image = user_profile.profile_img
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profile_img = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()

        if request.FILES.get('image') != None:
            image = request.FILES.get('image')
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profile_img = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        
        return redirect('settings')

    return render(request, 'setting.html', {'user_profile': user_profile})


def signup(request):
    if request.method=='POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        # print(username, email, password, password2)
        if password==password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already exists')
                return redirect('signup')

            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username already taken')
                return redirect('signup')

            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # Log user in and redirect to setting page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                # create a profile object from new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, userid=user_model.id)
                new_profile.save()
                messages.info(request, 'User Created')
                return redirect('settings')
        else:
            messages.info(request, 'Password not matching')
            return redirect('signup')
    
    else:
        return render(request, 'signup.html')


def signin(request):
    if request.method=='POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect('signin')
    else:
        return render(request, 'signin.html')


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')