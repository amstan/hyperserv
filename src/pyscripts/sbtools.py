def textcolor(color, text):
	if text:
		return '\fs\f' + str(color) + text + '\fr'
	else:
		return '\f' + str(color)
def green(text):
	return textcolor(0, text)
def blue(text):
	return textcolor(1, text)
def yellow(text):
	return textcolor(2, text)
def red(text):
	return textcolor(3, text)
def magenta(text):
	return textcolor(5, text)
def orange(text):
	return textcolor(6, text)
def white(text):
	return textcolor(10, text)

def colorstring(str, text):
	if str == 'green':
		return green(text)
	if str == 'blue':
		return blue(text)
	if str == 'yellow':
		return yellow(text)
	if str == 'red':
		return red(text)
	if str == 'magenta':
		return magenta(text)
	if str == 'orange':
		return orange(text)
	if str == 'white':
		return white(text)